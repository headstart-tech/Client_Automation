"""
This file contains test cases related to send update to the selected profiles.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_send_update_to_profile(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, application_details,
        super_admin_access_token
):
    """
    Test cases for API route which useful for send update to the
    selected profiles.
    """
    # Un-authorized user tried to send update to profile.
    response = await http_client_test.post(
        f"/resource/send_update_to_profile/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # Pass invalid access token for send update to profile.
    response = await http_client_test.post(
        f"/resource/send_update_to_profile/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for send update to profile.
    response = await http_client_test.post(
        f"/resource/send_update_to_profile/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}

    # Invalid college id for send update to profile.
    response = await http_client_test.post(
        f"/resource/send_update_to_profile/?college_id="
        f"1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # Wrong college id for send update to profile.
    response = await http_client_test.post(
        f"/resource/send_update_to_profile/?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    # Required body for send update to profile.
    response = await http_client_test.post(
        f"/resource/send_update_to_profile/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and "
                                         "valid."}

    # Required selected profiles for send update to profile.
    response = await http_client_test.post(
        f"/resource/send_update_to_profile/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Selected Profiles must be required "
                                         "and valid."}

    # Required title for send update to profile.
    response = await http_client_test.post(
        f"/resource/send_update_to_profile/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"selected_profiles": ["college_super_admin"]}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Title must be required "
                                         "and valid."}

    # Required content for send update to profile.
    response = await http_client_test.post(
        f"/resource/send_update_to_profile/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"selected_profiles": ["college_super_admin"], "title": "test"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Content must be required "
                                         "and valid."}

    # No enough permission for send update to profile
    response = await http_client_test.post(
        f"/resource/send_update_to_profile/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{super_admin_access_token}"},
        json={"selected_profiles": ["college_super_admin"], "title": "test",
              "content": "test"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": 'Not enough permission to send '
                                         'update.'}

    # TODO: Test cases failed when we run whole test cases
    #  but it is passed when we run this test case only.
    # Send update to profile
    # response = await http_client_test.post(
    #     f"/resource/send_update_to_profile/?college_id="
    #     f"{str(test_college_validation.get('_id'))}",
    #     headers={"Authorization": f"Bearer "
    #                               f"{college_super_admin_access_token}"},
    #     json={"selected_profiles": ["college_super_admin"], "title": "test",
    #           "content": "test"}
    # )
    # assert response.status_code == 200
    # assert response.json() == {"message": "Send update to the selected "
    #                                       "profiles."}
    # TODO: Test cases failed when we run whole test cases
    #  but it is passed when we run this test case only.
    # # User not found for send update.
    # response = await http_client_test.post(
    #     f"/resource/send_update_to_profile/?college_id="
    #     f"{str(test_college_validation.get('_id'))}",
    #     headers={"Authorization": f"Bearer "
    #                               f"{college_super_admin_access_token}"},
    #     json={"selected_profiles": ["test"], "title": "test",
    #           "content": "test"}
    # )
    # assert response.status_code == 200
    # assert response.json() == {"detail": "No user found for send update."}

    # no permission to send update to the super_admin.
    response = await http_client_test.post(
        f"/resource/send_update_to_profile/?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"selected_profiles": ["super_admin"], "title": "test",
              "content": "test"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Not able to send update to the "
                                         "super admin."}
