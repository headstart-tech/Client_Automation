"""
This file contains test cases for add/update leave of counselor
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_leave_college_counselor_not_authenticate(http_client_test, setup_module):
    """
    Not authenticated for add/update leave of counselor
    """
    response = await http_client_test.post(
        "/counselor/leave_college_counselor?feature_key={feature_key}",
        headers={"Authorization": "wrong Bearer"},
        json={
            "counselor_id": "62bfd13a5ce8a398ad101bd7",
            "dates": ["2022-08-10", "2022-05-13"],
        },
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_leave_college_counselor_wrong_counselor_id(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module
):
    """
    wrong counselor id
    :param http_client_test:
    :param setup_module:
    :return:
    """
    response = await http_client_test.post(
        f"/counselor/leave_college_counselor?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "counselor_id": "62bfd13a5ce8a398ad1017",
            "dates": ["2022-08-10", "2022-05-13"],
        },
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "counselor not found"


@pytest.mark.asyncio
async def test_leave_college_counselor(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module,
        test_counselor_validation
):
    """
    Add leave of counselor
    """
    response = await http_client_test.post(
        f"/counselor/leave_college_counselor?college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "counselor_id": str(test_counselor_validation.get('_id')),
            "dates": ["2022-08-10", "2022-05-13"],
        },
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data inserted successfully"
    assert response.json()["data"] == [True]
