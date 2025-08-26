"""
This file contains the test cases of qa reviews in qa manager panel.
"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_qa_reviews_unauthenticated(
    http_client_test
):
    """
    Unauthenticated user
    """
    response = await http_client_test.post(f"/qa_manager/qa/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_qa_reviews_wrong_token(
    http_client_test
):
    """
    Wrong token
    """
    response = await http_client_test.post(
        f"/qa_manager/qa/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_qa_reviews_unauthorized_token(
    http_client_test, access_token, setup_module, test_college_validation
):
    """
    Unauthorized token
    """
    response = await http_client_test.post(
        f"/qa_manager/qa/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_qa_reviews_wrong_college_id(
    http_client_test, access_token, setup_module
):
    """
    wrong college id
    """
    response = await http_client_test.post(
        f"/qa_manager/qa/"
        f"?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}


# Todo: Following test case is failing for now
# @pytest.mark.asyncio
# async def test_qa_reviews_authorized_token(
#     http_client_test, college_super_admin_access_token, setup_module, test_college_validation
# ):
#     """
#     authorized token
#     """
#     response = await http_client_test.post(
#         f"/qa_manager/counsellor/"
#         f"?college_id={str(test_college_validation.get('_id'))}",
#         headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
#     )
#     assert response.status_code == 200
