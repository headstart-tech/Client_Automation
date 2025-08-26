"""
This file contains test cases related to student routes/endpoints
"""
import inspect
from pathlib import Path, PurePath

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

def get_file_path():
    """
    This functions returns the absolute path of result.pdf file
    """
    file_path = Path(inspect.getfile(inspect.currentframe())).resolve()
    root_folder_path = PurePath(file_path).parent.parent.parent
    college_csv = PurePath(root_folder_path, Path(rf"tests/student/result.pdf"))
    return college_csv


@pytest.mark.asyncio
async def test_get_student_primary_details_not_authenticated(
        http_client_test, test_college_validation, setup_module
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/student/get_students_primary_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_student_primary_details_bad_credentials(
        http_client_test, test_college_validation, setup_module
):
    """
    Bad token for get student primary details
    """
    response = await http_client_test.get(
        f"/student/get_students_primary_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_student_primary_details_no_permission(
        http_client_test, test_college_validation, college_counselor_access_token, setup_module
):
    """
    No permission for get student primary details
    """
    response = await http_client_test.get(
        f"/student/get_students_primary_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_student_primary_details(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Get student primary details
    """
    response = await http_client_test.get(
        f"/student/get_students_primary_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["user_name"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_student_details_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/student/get_students_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_student_details_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for get student details
    """
    response = await http_client_test.get(
        f"/student/get_student_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


@pytest.mark.asyncio
async def test_get_student_details_no_permission(
        http_client_test, test_college_validation, college_counselor_access_token, setup_module
):
    """
    No permission for get student details
    """
    response = await http_client_test.get(
        f"/student/get_students_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_student_details(http_client_test, test_college_validation, access_token, setup_module):
    """
    Get student details
    """
    response = await http_client_test.get(
        f"/student/get_students_details/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Students data fetched successfully."


@pytest.mark.asyncio
async def test_add_or_update_basic_details_not_authenticated(
        http_client_test, test_college_validation, setup_module
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/student/basic_details/BSc/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_add_or_update_basic_details_bad_credentials(
        http_client_test, test_college_validation, setup_module
):
    """
    Bad token for add or update basic details
    """
    response = await http_client_test.put(
        f"/student/basic_details/BSc/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_add_or_update_basic_details_no_permission(
        http_client_test, test_college_validation,
        college_counselor_access_token,
        test_student_basic_details,
        setup_module,
):
    """
    No permission for add or update basic details
    """
    response = await http_client_test.put(
        f"/student/basic_details/BSc/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_counselor_access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_basic_details,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_add_or_update_basic_details(
        http_client_test, test_college_validation, access_token, test_student_basic_details, setup_module,
        test_course_validation
):
    """
    Add or update basic details
    """
    response = await http_client_test.put(
        f"/student/basic_details/{test_course_validation.get('course_name')}/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_basic_details,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Basic details added or updated successfully"


@pytest.mark.asyncio
async def test_add_or_update_basic_details_course_not_found(
        http_client_test, test_college_validation, access_token, test_student_basic_details, setup_module
):
    """
    Course not found. for add or update basic details
    """
    response = await http_client_test.put(
        f"/student/basic_details/bsc/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_basic_details,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "course not found."


@pytest.mark.asyncio
async def test_add_or_update_parent_details_not_authenticated(
        http_client_test, test_college_validation, setup_module
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/student/parent_details/BSc/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_add_or_update_parent_details_bad_credentials(
        http_client_test, test_college_validation, setup_module
):
    """
    Bad token for add or update parent details
    """
    response = await http_client_test.put(
        f"/student/parent_details/BSc/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_add_or_update_parent_details_no_permission(
        http_client_test,
        test_college_validation,
        college_super_admin_access_token,
        test_student_parent_details,
        setup_module, test_course_validation
):
    """
    No permission for add or update parent details
    """
    response = await http_client_test.put(
        f"/student/parent_details/{test_course_validation.get('course_name')}/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_super_admin_access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_parent_details,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_add_or_update_parent_details(
        http_client_test, test_college_validation, access_token, test_student_parent_details, setup_module,
        test_course_validation
):
    """
    Add or update parent details
    """
    response = await http_client_test.put(
        f"/student/parent_details/{test_course_validation.get('course_name')}/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_parent_details,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Parent details added or updated successfully"


@pytest.mark.asyncio
async def test_add_or_update_parent_details_course_not_found(
        http_client_test, test_college_validation, access_token, test_student_parent_details, setup_module
):
    """
    Course not found. for add or update parent details
    """
    response = await http_client_test.put(
        f"/student/parent_details/bsc/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_parent_details,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "course not found."


@pytest.mark.asyncio
async def test_add_or_update_address_details_not_authenticated(
        http_client_test, test_college_validation, setup_module
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/student/address_details/BSc/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_add_or_update_address_details_bad_credentials(
        http_client_test, test_college_validation, setup_module
):
    """
    Bad token for add or update address details
    """
    response = await http_client_test.put(
        f"/student/address_details/BSc/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_add_or_update_address_details_no_permission(
        http_client_test,
        test_college_validation,
        college_counselor_access_token,
        test_student_address_details,
        setup_module,
):
    """
    Add or update parent details
    """
    response = await http_client_test.put(
        f"/student/address_details/BSc/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_counselor_access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_address_details,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_add_or_update_address_details(
        http_client_test, test_college_validation, access_token, test_student_address_details, setup_module,
        test_course_validation
):
    """
    Add or update parent details
    """
    response = await http_client_test.put(
        f"/student/address_details/{test_course_validation.get('course_name')}/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_address_details,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Address details added or updated successfully."


@pytest.mark.asyncio
async def test_add_or_update_address_details_course_not_found(
        http_client_test, test_college_validation, access_token, test_student_address_details, setup_module
):
    """
    Course not found. for add or update address details
    """
    response = await http_client_test.put(
        f"/student/address_details/bsc/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_address_details,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "course not found."


@pytest.mark.asyncio
async def test_add_or_update_education_details_not_authenticated(
        http_client_test, test_college_validation, setup_module
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/student/education_details/BSc/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_add_or_update_education_details_bad_credentials(
        http_client_test, test_college_validation, setup_module
):
    """
    Bad token for add or update education details
    """
    response = await http_client_test.put(
        f"/student/education_details/BSc/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_add_or_update_education_details_no_permission(
        http_client_test,
        test_college_validation,
        college_counselor_access_token,
        test_student_education_details,
        setup_module,
        test_course_validation
):
    """
    No permission for add or update education details
    """
    response = await http_client_test.put(
        f"/student/education_details/{test_course_validation.get('course_name')}/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {college_counselor_access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_education_details,
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_add_or_update_education_details(
        http_client_test, test_college_validation, access_token, test_student_education_details, setup_module,
        test_course_validation
):
    """
    Add or update education details
    """
    response = await http_client_test.put(
        f"/student/education_details/{test_course_validation.get('course_name')}/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_education_details,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Education details added or updated successfully"


@pytest.mark.asyncio
async def test_add_or_update_education_details_course_not_found(
        http_client_test, test_college_validation, access_token, test_student_education_details, setup_module
):
    """
    Course not found. for add or update education details
    """
    response = await http_client_test.put(
        f"/student/education_details/bsc/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        },
        json=test_student_education_details,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Course not found"


@pytest.mark.asyncio
async def test_get_student_document_not_authenticated(http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/student/get_document/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_student_document_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for add or update document details
    """
    response = await http_client_test.get(
        f"/student/get_document/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_student_document_no_permission(
        http_client_test, test_college_validation, college_counselor_access_token, setup_module
):
    """
    No permission for add or update document
    """
    response = await http_client_test.get(
        f"/student/get_document/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_student_document(http_client_test, test_college_validation, access_token, setup_module):
    """
    Add or update document
    """
    response = await http_client_test.get(
        f"/student/get_document/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."


@pytest.mark.asyncio
async def test_upload_student_documents_not_authenticated(
        http_client_test, test_college_validation, setup_module
):
    """
    Not authenticated when try to upload student documents
    """
    response = await http_client_test.post(
        f"/student/document_details/123456789012345678901234/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_upload_student_documents_bad_token(
        http_client_test, test_college_validation, setup_module):
    """
    Bad token when try to upload student documents
    :return:
    """
    response = await http_client_test.post(
        f"/student/document_details/123456789012345678901234/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_upload_student_documents_no_permission(
        http_client_test, test_college_validation,
        college_counselor_access_token, setup_module, application_details
):
    """
    No permission when try to upload student documents
    """
    with open(get_file_path(), "rb") as f:
        file = {"files": f}
        response = await http_client_test.post(
            f"/student/document_details/{str(application_details.get('_id'))}/"
            f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {college_counselor_access_token}"},
            files=file,
        )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


# Todo: Need to check below test case later on
# @pytest.mark.asyncio
# async def test_upload_student_documents(http_client_test, test_college_validation, access_token, setup_module,
#                                         application_details):
#     """
#     Upload student documents
#     """
#     from app.database.configuration import DatabaseConfiguration
#     await DatabaseConfiguration().studentApplicationForms.update_one(
#         {"_id": application_details.get("_id")}, {"$set": {"payment_info.status": "captured"}}
#     )
#     with open(get_file_path(), "rb") as f:
#         file = {"files": f}
#         response = await http_client_test.post(
#             f"/student/document_details/{str(application_details.get('_id'))}/?college_id={str(test_college_validation.get('_id'))}",
#             headers={"Authorization": f"Bearer {access_token}"},
#             files=file,
#         )
#     assert response.status_code == 200
#     assert response.json()["message"] == "All files are uploaded."


@pytest.mark.asyncio
async def test_upload_student_documents_course_fee_not_paid(
        http_client_test, test_college_validation, access_token, setup_module,
        application_details
):
    """
    Course fee not paid when try to upload student documents
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentApplicationForms.update_one(
        {"_id": application_details.get("_id")},
        {"$unset": {"payment_info.status": True}}
    )
    with open(get_file_path(), "rb") as f:
        file = {"files": f}
        response = await http_client_test.post(
            f"/student/document_details/{str(application_details.get('_id'))}/"
            f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {access_token}"},
            files=file,
        )
    assert response.status_code == 402
    assert response.json()["detail"] == "Application fee not paid."

@pytest.mark.asyncio
async def test_upload_student_documents_course_not_found(
        http_client_test, test_college_validation, access_token, setup_module,
        application_details
):
    """
    Course not found. when try to upload student documents
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().course_collection.delete_one(
        {"_id": application_details.get("course_id")}
    )
    with open(get_file_path(), "rb") as f:
        file = {"files": f}
        response = await http_client_test.post(
            f"/student/document_details/{str(application_details.get('_id'))}/"
            f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {access_token}"},
            files=file,
        )
    assert response.status_code == 404
    assert response.json()["detail"] == "course not found."
    await DatabaseConfiguration().studentApplicationForms.delete_one(
        {"_id": application_details.get("_id")}
    )


@pytest.mark.asyncio
async def test_student_change_password_not_authenticated(
        http_client_test, test_college_validation, setup_module
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/student/change_password/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_student_change_password_bad_credentials(http_client_test, test_college_validation, setup_module):
    """
    Bad token for student change password
    """
    response = await http_client_test.put(
        f"/student/change_password/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_student_change_password_current_password_required(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Required current password for student change password
    """
    response = await http_client_test.put(
        f"/student/change_password/?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Current Password must be required and valid."}


@pytest.mark.asyncio
async def test_student_change_password_incorrect_current_password(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Incorrect current password for student change password
    """
    response = await http_client_test.put(
        f"/student/change_password/?current_password=test&new_password=getmein1&feature_key={feature_key}"
        f"&confirm_password=getmein1&college_id={str(test_college_validation.get('_id'))}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Current password is incorrect."


@pytest.mark.asyncio
async def test_student_change_password_new_password_invalid(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Invalid new password for student change password
    """
    response = await http_client_test.put(
        f"/student/change_password/?current_password=getmein&new_password=getmein&feature_key={feature_key}"
        f"&confirm_password=getmein&college_id={str(test_college_validation.get('_id'))}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "New Password must be "
                                         "required and valid."}


@pytest.mark.asyncio
async def test_student_change_password_mismatch_password(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Mismatch password for student change password
    """
    response = await http_client_test.put(
        f"/student/change_password/?current_password=getmein"
        f"&new_password=getmein1&confirm_password=getmein&feature_key={feature_key}"
        f"&college_id={str(test_college_validation.get('_id'))}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": "New Password and Confirm Password doesn't match."
    }


@pytest.mark.asyncio
async def test_student_change_password(http_client_test, test_college_validation, access_token, setup_module):
    """
    Student change password
    """
    response = await http_client_test.put(
        f"/student/change_password/?current_password=getmein&new_password=getmein1&confirm_password=getmein1"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Your password has been updated successfully."


@pytest.mark.asyncio
async def test_student_change_password_repeat_password(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Repeat password for student change password
    """
    response = await http_client_test.put(
        f"/student/change_password/?current_password=getmein1&new_password=getmein1&feature_key={feature_key}"
        f"&confirm_password=getmein1&college_id={str(test_college_validation.get('_id'))}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 422
    assert (
        response.json()["detail"]
        == "Your new password should not match with last password."
    )
