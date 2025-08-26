"""
This file contains test case regarding student application
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_current_student_applications_not_authorized(
        http_client_test, test_college_validation, setup_module
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/student_application/get_student_application?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_current_student_applications_bad_credentials(
        http_client_test, test_college_validation, setup_module
):
    """
    Bad token for add student query
    """
    response = await http_client_test.get(
        f"/student_application/get_student_application?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_current_student_applications_no_permission(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    No permission for get current student applications
    """
    response = await http_client_test.get(
        f"/student_application/get_student_application?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not enough permissions"


# Todo: Need to check below test case later on
# @pytest.mark.asyncio
# async def test_get_current_student_applications(
#         http_client_test, test_college_validation, access_token, setup_module,
#         application_details
# ):
#     """
#     Get current student applications
#     """
#     response = await http_client_test.get(
#         f"/student_application/get_student_application?college_id={str(test_college_validation.get('_id'))}",
#         headers={"Authorization": f"Bearer {access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Applications data fetched successfully."


@pytest.mark.asyncio
async def test_check_application_form_status_not_authorized(
        http_client_test, test_college_validation, setup_module
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/student_application/check_form_status/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_check_application_form_status_bad_credentials(
        http_client_test, test_college_validation, setup_module
):
    """
    Bad token for check application form status
    """
    response = await http_client_test.get(
        f"/student_application/check_form_status/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_check_application_form_status_field_required(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Field required for check application form status
    """
    response = await http_client_test.get(
        f"/student_application/check_form_status/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Application Id must be required and valid."}


@pytest.mark.asyncio
async def test_check_application_form_status_no_permission(
        http_client_test, test_college_validation, super_admin_access_token, setup_module, application_details
):
    """
    No permission for check application form status
    """
    response = await http_client_test.get(
        f"/student_application/check_form_status/?application_id={str(application_details.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_check_application_form_status(
        http_client_test, test_college_validation, access_token, setup_module, application_details
):
    """
    Check application form status
    """
    response = await http_client_test.get(
        f"/student_application/check_form_status/?application_id={str(application_details.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Form status is Incomplete"


@pytest.mark.asyncio
async def test_check_application_form_status_application_not_found(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Check application form status not found
    """
    response = await http_client_test.get(
        f"/student_application/check_form_status/?application_id=12c6d899fe03e541b3660781"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"


@pytest.mark.asyncio
async def test_application_declaration_not_authorized(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/student_application/declaration/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_application_declaration_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for application declaration
    """
    response = await http_client_test.post(
        f"/student_application/declaration/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_application_declaration_field_required(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Field required for application declaration
    """
    response = await http_client_test.post(
        f"/student_application/declaration/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Application Id must be required and valid."}


@pytest.mark.asyncio
async def test_application_declaration_no_permisssion(
        http_client_test, test_college_validation, super_admin_access_token, setup_module, application_details
):
    """
    No permission for application declaration
    """
    response = await http_client_test.post(
        f"/student_application/declaration/?application_id={str(application_details.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_application_declaration(http_client_test, test_college_validation, access_token, setup_module):
    """
    Application declaration
    """
    response = await http_client_test.post(
        f"/student_application/declaration/?application_id=12a8c5954035e93c7ff12345"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Application not found"}


@pytest.mark.asyncio
async def test_application_declaration_pending_form(
        http_client_test, test_college_validation, access_token, setup_module, application_details
):
    """
    Declaration pending form
    """
    response = await http_client_test.post(
        f"/student_application/declaration/?application_id={str(application_details.get('_id'))}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"pending": "Your form is still pending."}

# TODO Check the test case
@pytest.mark.skip
async def test_application_declaration_no_permission(
        http_client_test, test_college_validation, access_token, setup_module, application_details
):
    """
    No permission for application declaration
    """
    response = await http_client_test.post(
        f"/student_application/declaration/?application_id={str(application_details.get('_id'))}"
        f"&short=true&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Documents not uploaded"}


@pytest.mark.asyncio
async def test_update_application_payment_status_not_authorized(
        http_client_test, test_college_validation, setup_module, application_details
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/student_application/update_payment_status/{str(application_details.get('_id'))}/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_application_payment_status_bad_credentials(
        http_client_test, test_college_validation, setup_module, application_details
):
    """
    Bad token for update application payment status
    """
    response = await http_client_test.put(
        f"/student_application/update_payment_status/{str(application_details.get('_id'))}/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


# ToDo - Following commented test case giving error when running all test cases, otherwise working fine.
# @pytest.mark.asyncio
# async def test_update_application_payment_status(
#         http_client_test, test_college_validation, access_token, setup_module, application_details
# ):
#     """
#     Update application payment status
#     """
#     response = await http_client_test.put(
#         f"/student_application/update_payment_status/{str(application_details.get('_id'))}/?course_fee=100000&payment_id=pay_KBioqqepq6qsWG&order_id=order_KBioPy4e6BClSp&rezorpay_signature=48654bf787ba2f983f05018f8fe10865d84670cf8aa688376a4924f12a909974&college_id={str(test_college_validation.get('_id'))}",
#         headers={"Authorization": f"Bearer {access_token}"},
#     )
#     assert response.status_code == 200
#     assert (
#         response.json()["message"] == "Payment details added and updated successfully."
#     )


@pytest.mark.asyncio
async def test_update_application_payment_status_course_fee_not_found(
        http_client_test, test_college_validation, access_token, setup_module, application_details
):
    """
    Update application payment status Application not found
    """
    response = await http_client_test.put(
        f"/student_application/update_payment_status/{str(application_details.get('_id'))}/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Course Fee must be required and valid."


@pytest.mark.asyncio
async def test_get_all_course_of_current_user_not_authorized(
        http_client_test, test_college_validation, setup_module
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/student_application/get_all_course_of_current_user"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_all_course_of_current_user_bad_credentials(
        http_client_test, test_college_validation, setup_module
):
    """
    Bad token for get all course of current user
    """
    response = await http_client_test.get(
        f"/student_application/get_all_course_of_current_user"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_all_course_of_current_user_no_permission(
        http_client_test, test_college_validation, super_admin_access_token, setup_module
):
    """
    No permission for get all course of current user
    """
    response = await http_client_test.get(
        f"/student_application/get_all_course_of_current_user"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_all_course_of_current_user(
        http_client_test, test_college_validation, access_token, setup_module, test_student_validation
):
    """
    Get all course of current user
    """
    response = await http_client_test.get(
        f"/student_application/get_all_course_of_current_user"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert "college_id" in response.json()[0]
