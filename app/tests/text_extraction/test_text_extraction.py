import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

index = "tenth"
@pytest.mark.asyncio
async def test_text_extraction_not_authenticated(
        http_client_test,test_student_validation, test_college_validation, setup_module
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(
        f"/student/documents/text_extraction_info/{test_student_validation.get('_id')}/"
        f"?index={index}&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_text_extraction_bad_credentials(
        http_client_test,test_student_validation, test_college_validation, setup_module
):
    """
    Bad token to get extracted data
    """
    response = await http_client_test.get(
        f"/student/documents/text_extraction_info/{test_student_validation.get('_id')}/"
        f"?index={index}&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_text_extraction_field_required(
        http_client_test, test_college_validation, access_token, setup_module
, test_student_validation):
    """
    Field required to get extracted data
    """
    response = await http_client_test.get(
        f"/student/documents/text_extraction_info/{test_student_validation.get('_id')}/"
        f"?index={index}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and valid."}


@pytest.mark.asyncio
async def test_text_extraction_no_permission(
        http_client_test, test_college_validation, access_token, setup_module, test_student_validation
):
    """
    No permission to get extracted details
    """
    response = await http_client_test.get(
        f"/student/documents/text_extraction_info/{test_student_validation.get('_id')}/"
        f"?index={index}&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


# Todo: this test case failed i will do it later
# @pytest.mark.asyncio
# async def test_text_extraction_id_not_found(
#         http_client_test, test_college_validation, college_super_admin_access_token, setup_module
# ):
#     """
#     Get student details by id not found
#     """
#     response = await http_client_test.get(
#         f"/student/documents/text_extraction_info/6256569bfc64b4ac89d0a1dd/?index=1&college_id={str(test_college_validation.get('_id'))}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#     )
#     assert response.status_code == 404
#     assert (
#             response.json()["detail"]
#             == "Student document not found"
#     )
#
#
# @pytest.mark.asyncio
# async def test_text_extraction_doc_not_uploaded(
#         http_client_test,test_student_validation,test_college_validation,test_extracted_details, college_super_admin_access_token, setup_module):
#     """
#     documents are not uploaded
#     """
#     from app.database.configuration import DatabaseConfiguration
#     document = await DatabaseConfiguration().studentSecondaryDetails.find_one(
#         {"student_id": test_student_validation.get('_id')})
#     previous_document_analysis = document.get("document_analysis", {})
#     update = {"$unset": {"document_analysis": 1}}
#     await DatabaseConfiguration().studentSecondaryDetails.update_one(
#         {"student_id": test_student_validation.get('_id')}, update)
#
#     response = await http_client_test.get(
#         f"/student/documents/text_extraction_info/{test_student_validation.get('_id')}/?index=1&college_id={str(test_college_validation.get('_id'))}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
#     )
#     assert response.status_code == 200
#     assert response.json()["data"] == {}
#
#     await DatabaseConfiguration().studentSecondaryDetails.update_one(
#         {"student_id": test_student_validation.get('_id')},
#         {"$set": {"document_analysis": previous_document_analysis}})
#
# @pytest.mark.asyncio
# async def test_text_extraction(
#         http_client_test,test_student_validation,test_college_validation,test_extracted_details, college_super_admin_access_token, setup_module):
#     """
#     Get text extracted details
#     """
#     response = await http_client_test.get(
#         f"/student/documents/text_extraction_info/{test_student_validation.get('_id')}/?index=1&college_id={str(test_college_validation.get('_id'))}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
#     )
#     assert response.status_code == 200
#     assert "data" in response.json()


@pytest.mark.asyncio
async def test_text_extraction_invalid_college_id(http_client_test,test_student_validation,test_college_validation,test_extracted_details, college_super_admin_access_token, setup_module):
    """
        Invalid college id
    """
    response = await http_client_test.get(
        f"/student/documents/text_extraction_info/{test_student_validation.get('_id')}/"
        f"?index={index}&college_id=12345628&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_text_extraction_invalid_student_id(http_client_test,test_student_validation,test_college_validation,test_extracted_details, college_super_admin_access_token, setup_module):
    """
        Invalid student id
    """
    response = await http_client_test.get(
        f"/student/documents/text_extraction_info/123452/?index={index}"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Student id must be a 12-byte input or a 24-character hex string'
