"""
This file contains test cases regarding for get student program queries pdf.
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_student_program_queries_pdf(
        http_client_test, test_college_validation, query_details,
        test_course_validation, access_token, college_super_admin_access_token,
        setup_module, test_student_validation):
    """
    Test cases regarding for get student program queries pdf.
    """
    college_id = str(test_college_validation.get('_id'))
    # Not authenticated if user not logged in
    response = await http_client_test.post(
        f"/query/based_on_program/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Bad token for get student program queries pdf.
    response = await http_client_test.post(
        f"/query/based_on_program/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    # College id required for get student program queries pdf.
    response = await http_client_test.post(
        f"/query/based_on_program/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required "
                                         "and valid."}

    # Required student id for get student program queries pdf.
    response = await http_client_test.post(
        f"/query/based_on_program/?"
        f"college_id={college_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Student Id must be required "
                                         "and valid."}

    student_id = str(test_student_validation.get('_id'))
    # Required course name for get student program queries pdf.
    response = await http_client_test.post(
        f"/query/based_on_program/?"
        f"college_id={college_id}&student_id={student_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Course Name must be required "
                                         "and valid."}

    course_name = test_course_validation.get("course_name")
    # No permission for get student program queries pdf.
    response = await http_client_test.post(
        f"/query/based_on_program/?"
        f"college_id={college_id}&course_name={course_name}&student_id="
        f"{student_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}

    # Invalid college id for get student program queries pdf.
    response = await http_client_test.post(
        f"/query/based_on_program/?college_id=1234567890&course_name="
        f"{course_name}&student_id={student_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == \
           {"detail": "College id must be a 12-byte input or a "
                      "24-character hex string"}

    # College not found for get student program queries pdf.
    response = await http_client_test.post(
        f"/query/based_on_program/"
        f"?college_id=123456789012345678901234&course_name={course_name}"
        f"&student_id={student_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}

    # Get student program queries pdf.
    response = await http_client_test.post(
        f"/query/based_on_program/?college_id={college_id}&course_name="
        f"{course_name}&student_id={student_id}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    # assert "pdf_url" in response.json()

    # Student program queries not found
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().queries.delete_many({})
    response = await http_client_test.post(
        f"/query/based_on_program/?course_name={course_name}&"
        f"student_id={student_id}&college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Student program-wise queries "
                                         "not found."}

    # Invalid student id for get student queries pdf
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().queries.delete_many({})
    response = await http_client_test.post(
        f"/query/based_on_program/?course_name={course_name}&student_id=1233"
        f"&college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == \
           {"detail": "Student id `1233` must be a 12-byte input or a "
                      "24-character hex string"}

    # Wrong student id for get student queries pdf
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().queries.delete_many({})
    response = await http_client_test.post(
        f"/query/based_on_program/?course_name={course_name}&student_id="
        f"123456789012345678901234&college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json() == \
           {"detail": "Student not found"}

    # Wrong course name for get student queries pdf
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().queries.delete_many({})
    response = await http_client_test.post(
        f"/query/based_on_program/?course_name=vcf&student_id="
        f"{student_id}&college_id={college_id}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 404
    assert response.json() == \
           {"detail": "Course not found"}
