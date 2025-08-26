"""
This file contains test cases related to get application steps count
with/without counselor filter.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_step_wise_data(
        http_client_test, test_college_validation, setup_module,
        college_super_admin_access_token, application_details, start_end_date, test_student_data
):
    """
    Test cases for API route which useful for get application steps count data.
    """
    # Un-authorized user tried to get application steps count data.
    response = await http_client_test.post(
        f"/lead/step_wise_data?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    # Pass invalid access token for get application steps count data.
    response = await http_client_test.post(
        f"/lead/step_wise_data?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Required college id for get application steps count data.
    response = await http_client_test.post(
        f"/lead/step_wise_data?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}

    # Invalid college id for get application steps count data.
    response = await http_client_test.post(
        f"/lead/step_wise_data?college_id="
        f"1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

    # Wrong college id for get application steps count data.
    response = await http_client_test.post(
        f"/lead/step_wise_data?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    def validate_successful_data(data, invalid_response=False):
        """Validate successful data of API"""
        assert data.status_code == 200
        data = data.json()
        assert data['message'] == "Application steps count data fetch successfully."
        for item in ["step", "application"]:
            assert item in data['data'][0][0]
        if invalid_response:
            assert data['data'][0][0]["application"] == 0

    # Get application steps count data.
    response = await http_client_test.post(
        f"/lead/step_wise_data?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    validate_successful_data(response)

    # Get application steps count data by date_range
    response = await http_client_test.post(
        f"/lead/step_wise_data?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={
            "date_range": start_end_date
        }
    )
    validate_successful_data(response)

    # Get application steps count data by program name
    response = await http_client_test.post(
        f"/lead/step_wise_data?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={
            "program_name": [
  {
    "course_id": str(application_details.get("course_id")),
    "course_specialization": application_details.get("spec_name1")
  }
]
        }
    )
    validate_successful_data(response)

    # Get application steps count data by source
    response = await http_client_test.post(
        f"/lead/step_wise_data?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"source": [test_student_data.get("utm_source")]}
    )
    validate_successful_data(response)

    # Get application steps count data by wrong date_range
    response = await http_client_test.post(
        f"/lead/step_wise_data?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={
            "date_range": {"start_date": "1990-01-01", "end_date": "1990-01-01"}
        }
    )
    validate_successful_data(response, invalid_response=True)

    # Get application steps count data by wrong program name
    response = await http_client_test.post(
        f"/lead/step_wise_data?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={
            "program_name": [
                {
                    "course_id": "123",
                    "course_specialization": "test"
                }
            ]
        }
    )
    assert response.status_code == 422
    assert (response.json()['detail'] ==
            "Course id `123` must be a 12-byte input or a 24-character hex string")

    # Get application steps count data by wrong source
    response = await http_client_test.post(
        f"/lead/step_wise_data?college_id="
        f"{str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={"source": ["12"]}
    )
    validate_successful_data(response, invalid_response=True)
