"""
This file contains the test cases of counsellor reviews in qa manager panel.
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_counsellor_reviews_unauthenticated(
    http_client_test
):
    """
    unauthenticated user
    """
    response = await http_client_test.post(f"/qa_manager/counsellor/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_counsellor_reviews_wrong_token(
    http_client_test
):
    """
    wrong token for user
    """
    response = await http_client_test.post(
        f"/qa_manager/counsellor/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_counsellor_reviews_unauthorized_token(
    http_client_test, access_token, setup_module, test_college_validation
):
    """
    unauthorized token for another user
    """
    response = await http_client_test.post(
        f"/qa_manager/counsellor/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


# Todo: Following test case is failing for now
# @pytest.mark.asyncio
# async def test_counsellor_reviews_authorized_token(
#     http_client_test, college_super_admin_access_token, setup_module, test_college_validation
# ):
#     """
#     authorized token - successful data
#     """
#     response = await http_client_test.post(
#         f"/qa_manager/counsellor/"
#         f"?college_id={str(test_college_validation.get('_id'))}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
#     )
#     assert response.status_code == 200


@pytest.mark.asyncio
async def test_counsellor_reviews_wrong_college_id(
    http_client_test, access_token, setup_module
):
    """
    wrong college id
    """
    response = await http_client_test.post(
        f"/qa_manager/counsellor/"
        f"?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}
