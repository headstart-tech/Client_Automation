"""
this file testing display offline data route
"""
import random

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_display_offline_data_authentication(http_client_test, test_college_validation, setup_module):
    """
    Checking authentication when give wrong token
    """
    response = await http_client_test.put(
        f"/manage/display_offline/?page_num=1&page_size=25&"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": "wrong token"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_display_offline_data(
        http_client_test, test_college_validation, college_super_admin_access_token, setup_module, start_end_date
):
    """
    Checking with filter and date range
    """
    response = await http_client_test.put(
        f"/manage/display_offline/?page_num=1&page_size=25&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "date_range": start_end_date
        },
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetched successfully"


@pytest.mark.asyncio
async def test_display_offline_data_json(
        http_client_test,
        test_college_validation,
        setup_module,
        college_super_admin_access_token,
        test_user_validation,
):
    """
    Checking response, send payload user object id
    """
    response = await http_client_test.put(
        f"/manage/display_offline/?page_num=1&page_size=25&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={"imported_by": [str(test_user_validation.get("_id"))]},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetched successfully"


@pytest.mark.asyncio
async def test_display_offline_data_full_json(
        http_client_test,
        test_college_validation,
        setup_module,
        college_super_admin_access_token,
        test_user_validation,
        start_end_date
):
    """
    Checking response, send payload with all filter
    """
    response = await http_client_test.put(
        f"/manage/display_offline/?page_num=1&page_size=25&college_id={str(test_college_validation.get('_id'))}"
        f"&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json={
            "imported_by": [str(test_user_validation.get("_id"))],
            "date_range": start_end_date,
            "import_status": random.choice(["completed", "pending"]),
        },
    )
    assert response.status_code == 200
    assert response.json()["message"] == "data fetched successfully"
