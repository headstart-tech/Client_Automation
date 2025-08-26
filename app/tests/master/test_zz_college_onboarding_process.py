import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()
# Todo: Need to update the testcase according to the updated API
@pytest.mark.asyncio
async def test_college_onboarding(
    setup_module,
    http_client_test,
    college_super_admin_access_token,
    client_automation_test_course_data,
    test_client_automation_college_additional_data,
    test_get_client,
    test_college_validation,
    test_college_configuration_data
):
    from app.database.configuration import DatabaseConfiguration

    """Creating College"""
    college_data = {
        "name": "Delhi Technical University",
        "email": "dtu@example.com",
        "phone_number": "8889995556",
        "associated_client": str(test_get_client.get("_id")),
        "address": {
            "address_line_1": "",
            "address_line_2": "",
            "country_code": "IN",
            "state_code": "MH",
            "city_name": "Pune",
        },
    }
    await DatabaseConfiguration().college_collection.delete_many(
        {"name": "Delhi Technical University"}
    )
    response = await http_client_test.post(
        f"/client_automation/add_college?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=college_data,
    )
    assert response.status_code == 200
    college_id = response.json().get("college_id")

    # TODO: ADD COLLEGE CONFIGURATION ADDITION
    """Adding season details for college"""
    response = await http_client_test.post(
        f"/college/add_college_configuration?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_college_configuration_data,
        params={"college_id": str(college_id)}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "College configuration added successfully"}

    # """Adding Course Details"""
    # response = await http_client_test.post(
    #     f"/client_automation/{str(college_id)}/add_course?feature_key={feature_key}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     json=client_automation_test_course_data,
    # )
    # assert response.status_code == 200
    # approval_id = response.json().get("approval_id")
    #
    # response = await http_client_test.put(
    #     f"/approval/update_status/{approval_id}?feature_key={feature_key}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     params={"status": "approve"},
    #     json={"remarks": "Looks good"},
    # )
    # assert response.status_code == 200
    # response = await http_client_test.put(
    #     f"/approval/update_status/{approval_id}?feature_key={feature_key}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     params={"status": "approve"},
    #     json={"remarks": "Looks good"},
    # )
    # assert response.status_code == 200

    """Create Registration Form"""
    student_signup_form = {
        "student_registration_form_fields": [
            {
                "field_name": "Your Full Name",
                "field_type": "text",
                "is_mandatory": True,
                "editable": False,
                "can_remove": False,
                "key_name": "full_name",
            },
            {
                "field_name": "Enter Email Address",
                "field_type": "email",
                "is_mandatory": True,
                "editable": False,
                "can_remove": True,
                "key_name": "email",
            },
            {
                "field_name": "Country Code",
                "field_type": "select",
                "editable": False,
                "can_remove": False,
                "key_name": "country_code",
                "options": ["+91", "+880"],
                "is_mandatory": True,
                "dependent_fields": {
                    "logical_fields": {
                        "+91": [
                            {
                                "field_name": "Mobile No",
                                "field_type": "number",
                                "editable": False,
                                "can_remove": False,
                                "is_mandatory": True,
                                "key": "mobile_no",
                            }
                        ],
                        "+880": [
                            {
                                "field_name": "Mobile No",
                                "field_type": "number",
                                "editable": False,
                                "can_remove": False,
                                "is_mandatory": True,
                                "key": "mobile_no",
                            }
                        ],
                    }
                },
            },
            {
                "field_name": "Country",
                "field_type": "select",
                "is_mandatory": False,
                "editable": True,
                "can_remove": True,
                "options": ["India"],
                "key_name": "country",
                "dependent_fields": {
                    "logical_fields": {
                        "India": {
                            "fields": [
                                {
                                    "field_name": "State",
                                    "field_type": "select",
                                    "is_mandatory": False,
                                    "editable": True,
                                    "can_remove": True,
                                    "options": ["All the state of India will be shown"],
                                    "key_name": "state_code",
                                },
                                {
                                    "field_name": "City",
                                    "field_type": "select",
                                    "is_mandatory": False,
                                    "editable": True,
                                    "can_remove": True,
                                    "options": ["All the City of India will be shown"],
                                    "key_name": "city",
                                },
                            ]
                        }
                    }
                },
            },
            {
                "field_name": "Course",
                "field_type": "select",
                "is_mandatory": False,
                "editable": True,
                "can_remove": False,
                "options": ["All the course of college will be shown"],
                "key_name": "course",
            },
        ]
    }
    response = await http_client_test.post(
        f"master/validate_registration_form?college_id={str(college_id)}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=student_signup_form,
    )
    approval_id = response.json().get("approval_id")

    response = await http_client_test.put(
        f"/approval/update_status/{approval_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"status": "approve"},
        json={"remarks": "Looks good"},
    )
    assert response.status_code == 200
    # response = await http_client_test.put(
    #     f"/approval/update_status/{approval_id}?feature_key={feature_key}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     params={"status": "approve"},
    #     json={"remarks": "Looks good"},
    # )
    # assert response.status_code == 200

    """Student Application Form"""
    # TODO: Add student application form

    """Additional Details"""
    response = await http_client_test.post(
        f"/college/additional_details?college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_client_automation_college_additional_data,
        params={"short_version": True},
    )
    assert response.status_code == 200
    approval_id = response.json().get("approval_id")

    response = await http_client_test.put(
        f"/approval/update_status/{approval_id}?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"status": "approve"},
        json={"remarks": "Looks good"},
    )
    assert response.status_code == 200
    # response = await http_client_test.put(
    #     f"/approval/update_status/{approval_id}?feature_key={feature_key}",
    #     headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    #     params={"status": "approve"},
    #     json={"remarks": "Looks good"},
    # )
    # assert response.status_code == 200

    """Add College Subscription (Screen)"""
    master_screen_id = await DatabaseConfiguration().master_screens.find_one(
        {"screen_type": "master_screen"},
        {"_id": 0, "created_at": 0, "updated_at": 0, "screen_type": 0},
    )
    if master_screen_id:
        screen_ids = list(master_screen_id.keys())

        response = await http_client_test.post(
            f"/client_automation/add_features_screen?college_id={str(college_id)}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
            json={
                "screen_details": [
                    {
                        "feature_id": str(screen_ids[0]),
                    }
                ]
            },
        )
        assert response.status_code == 200

        approval_id = response.json().get("approval_id")

        response = await http_client_test.put(
            f"/approval/update_status/{approval_id}?feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
            params={"status": "approve"},
            json={"remarks": "Looks good"},
        )
        assert response.status_code == 200
