"""This File Contains Test Cases for Adding College Configuration"""

import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

# Test Case: Add College Configuration Without Authentication
@pytest.mark.asyncio
async def test_add_college_configuration_unauthenticated(
    setup_module, http_client_test
):
    """Test Case: Add College Configuration Without Authentication"""
    payload = {"university_prefix_name": "DU"}
    response = await http_client_test.post(
        f"/college/add_college_configuration?feature_key={feature_key}", json=payload, params={"college_id": "123"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


# Test Case: Add College Configuration With Invalid Token
@pytest.mark.asyncio
async def test_add_college_configuration_invalid_token(http_client_test):
    """Test Case: Add College Configuration With Invalid Token"""
    payload = {"university_prefix_name": "DU"}
    response = await http_client_test.post(
        f"/college/add_college_configuration?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"},
        json=payload,
        params={"college_id": "123"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


# Test Case: Add College Configuration When User Lacks Permissions
@pytest.mark.asyncio
async def test_add_college_configuration_permission_denied(
    http_client_test,
    access_token,
    test_college_configuration_data,
    test_client_automation_college_id,
):
    """Test Case: Add College Configuration When User Lacks Permissions"""
    response = await http_client_test.post(
        f"/college/add_college_configuration?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=test_college_configuration_data,
        params={"college_id": str(test_client_automation_college_id)},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


# Test Case: Invalid Payload (Pydantic Validation Error)
@pytest.mark.asyncio
async def test_add_college_configuration_invalid_payload(
    http_client_test, super_admin_token, test_client_automation_college_id
):
    """Test Case: Invalid Payload (Missing Required Fields or Wrong Types)"""
    # seasons is expected to be a list, here we provide a string
    payload = {"seasons": "not_a_list"}
    response = await http_client_test.post(
        f"/college/add_college_configuration?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
        json=payload,
        params={"college_id": str(test_client_automation_college_id)},
    )
    assert response.status_code == 400


# Test Case: Successfully Add College Configuration
@pytest.mark.asyncio
async def test_add_college_configuration_success(
    http_client_test,
    college_super_admin_access_token,
    test_client_automation_college_id,
    test_college_configuration_data,
):
    """Test Case: Successfully Add College Configuration"""
    response = await http_client_test.post(
        f"/college/add_college_configuration?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json=test_college_configuration_data,
        params={"college_id": test_client_automation_college_id},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "College configuration added successfully"}

    """ Test Case: Successfully Get College Configuration """
    response = await http_client_test.get(
        f"/college/college_configuration?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        params={"college_id": test_client_automation_college_id}
    )
    assert response.status_code == 200

# Test Case: Get College Configuration Without Authentication
@pytest.mark.asyncio
async def test_get_college_configuration_unauthenticated(http_client_test):
    """ Test Case: Get College Configuration Without Authentication """
    response = await http_client_test.get(f"/college/college_configuration?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

# Test Case: Get College Configuration With Invalid Token
@pytest.mark.asyncio
async def test_get_college_configuration_invalid_token(http_client_test):
    """ Test Case: Get College Configuration With Invalid Token """
    response = await http_client_test.get(
        f"/college/college_configuration?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

# Test Case: Not Enough Permissions → 401
@pytest.mark.asyncio
async def test_get_college_configuration_not_enough_permissions(http_client_test, access_token, test_client_automation_college_id):
    """ Test Case: Not Enough Permissions → 401 """
    response = await http_client_test.get(
        f"/college/college_configuration?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"college_id": test_client_automation_college_id}

    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}
