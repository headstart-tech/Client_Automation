"""
This file contain test cases for get followup report
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_followup_report_not_authenticate(http_client_test, setup_module, test_college_validation):
    """
    Check authentication for get followup report
    """
    response = await http_client_test.put(
        f"/counselor/followup_report/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": "wrong bearer"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_followup_report_required_page_num(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, start_end_date
):
    """
    Page num required to get followup report
    """
    response = await http_client_test.put(
        f"/counselor/followup_report/?counselor_id=62bfd13a5ce8a398ad101bd7"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=start_end_date
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Page Num must be required and valid."


@pytest.mark.asyncio
async def test_followup_report_required_page_size(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, start_end_date
):
    """
    Page size required to get followup report
    """
    response = await http_client_test.put(
        f"/counselor/followup_report/?counselor_id=62bfd13a5ce8a398ad101bd7&page_num=1"
        f"&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=start_end_date,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Page Size must be required and valid."


# @pytest.mark.asyncio
# async def test_followup_report(
#         http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
#         test_counselor_validation, start_end_date
# ):
#     """
#     Get followup report
#     """
#     response = await http_client_test.put(
#         f"/counselor/followup_report/?counselor_id={test_counselor_validation.get('_id')}"
#         f"&page_num=1&page_size=5&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
#         json=start_end_date
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "data fetch successfully"
