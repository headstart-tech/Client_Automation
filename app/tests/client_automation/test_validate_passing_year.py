import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_validate_passing_year(http_client_test, setup_module, college_super_admin_access_token, access_token,
                                     test_college_validation, test_super_admin_validation
                                     ):
    """
    Test case for validating passing years.
    """

    # Not authenticated
    response = await http_client_test.post(f"/client_student_dashboard/validate_passing_year?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for validating passing year
    response = await http_client_test.post(
        f"/client_student_dashboard/validate_passing_year?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # Invalid tenth passing year
    tenth_passing_year=9999
    response = await http_client_test.post(
        f"/client_student_dashboard/validate_passing_year?tenth_passing_year={tenth_passing_year}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert "10th passing year must be at least 1 year before" in response.json()["detail"]

    # Valid passing years (all valid years for each field)
    valid_payload = {
        "tenth_passing_year": 2010,
        "twelfth_passing_year": 2012,
        "graduation_passing_year": 2015,
        "post_graduation_passing_year": 2018,
    }

    response = await http_client_test.post(
        f"/client_student_dashboard/validate_passing_year?tenth_passing_year=2010"
        f"&twelfth_passing_year=2012&graduation_passing_year=2015&post_graduation_passing_year=2018"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Valid passing year selection"

    # Invalid 10th passing year (invalid year)
    invalid_payload = {
        "tenth_passing_year": 9999,  # Invalid year
    }

    response = await http_client_test.post(
        f"/client_student_dashboard/validate_passing_year?tenth_passing_year=9999&feature_key={feature_key}",
        json=invalid_payload,
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert "10th passing year must be at least 1 year before" in response.json()["detail"]

    # Successful validation (with only the required field)
    response = await http_client_test.post(
        f"/client_student_dashboard/validate_passing_year?tenth_passing_year=2010&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Valid passing year selection"
