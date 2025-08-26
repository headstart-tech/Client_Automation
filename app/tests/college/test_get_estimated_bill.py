"""
This file contains test cases related to get estimated bill
"""
import pytest
from bson import ObjectId
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_estimated_bill_not_authenticated(http_client_test, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.get(f"/college/estimation_bill/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_estimated_bill_bad_credentials(http_client_test, setup_module):
    """
    Bad token for get estimated bill of college
    """
    response = await http_client_test.get(
        f"/college/estimation_bill/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_get_estimated_bill_no_permission(
        http_client_test, access_token, test_college_validation, setup_module
):
    """
    No permission for get estimated bill of college
    """
    response = await http_client_test.get(
        f"/college/estimation_bill/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


@pytest.mark.asyncio
async def test_get_estimated_bill(http_client_test, test_college_validation, client_manager_access_token, setup_module):
    """
    Get estimated bill of college
    """
    response = await http_client_test.get(
        f"/college/estimation_bill/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {client_manager_access_token}"})
    assert response.status_code == 200
    assert response.json()['message'] == "Get estimated bill."


@pytest.mark.asyncio
async def test_get_estimated_bill_no_found(http_client_test, client_manager_access_token, setup_module):
    """
    College not found for get estimated bill of college
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().college_collection.delete_many({})
    response = await http_client_test.get(
        f"/college/estimation_bill/?college_id=123456789012345678901234&feature_key={feature_key}",
            headers={"Authorization": f"Bearer {client_manager_access_token}"})
    assert response.status_code == 200
    assert response.json()['detail'] == "Colleges data not found."


""" Test Cases for Getting College Billing Details """

# Test Case: Get Billing Details Without Authentication
@pytest.mark.asyncio
async def test_get_billing_details_unauthenticated(http_client_test):
    """ Test Case: Get Billing Details Without Authentication """
    payload = {}
    response = await http_client_test.post(
        f"/college/get_billing_details/?feature_key={feature_key}", json=payload, params={"college_id": "123"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


# Test Case: Get Billing Details With Invalid Token
@pytest.mark.asyncio
async def test_get_billing_details_invalid_token(http_client_test):
    """ Test Case: Get Billing Details With Invalid Token """
    payload = {}
    response = await http_client_test.post(
        f"/college/get_billing_details/?feature_key={feature_key}",
        headers={"Authorization": "Bearer invalid_token"},
        json=payload, params={"college_id": "123"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


# Test Case: Get Billing Details With No Permission
@pytest.mark.asyncio
async def test_get_billing_details_no_permission(http_client_test, access_token, test_college_validation):
    """ Test Case: Get Billing Details With No Permission """
    payload = {"filters": "last_30_days"}
    response = await http_client_test.post(
        f"/college/get_billing_details/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
        json=payload, params={"college_id": str(test_college_validation.get('_id'))}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not enough permissions"}


# Test Case: Get Billing Details With Invalid Filter
@pytest.mark.asyncio
async def test_get_billing_details_invalid_filter(http_client_test, super_admin_token, test_college_validation):
    """ Test Case: Get Billing Details With Invalid Filter """
    payload = {"filters": "not_a_valid_filter"}
    response = await http_client_test.post(
        f"/college/get_billing_details/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
        json=payload, params={"college_id": str(test_college_validation.get('_id'))}
    )
    assert response.status_code == 400


# # Test Case: Get Billing Details Data Not Found (College Screen Missing)
# @pytest.mark.asyncio
# async def test_get_billing_details_not_found(http_client_test, super_admin_token):
#     """ Test Case: Get Billing Details Data Not Found (College Screen Missing) """
#     payload = {"from_date": "2023-01-01", "to_date": "2025-04-01"}
#     response = await http_client_test.post(
#         "/college/get_billing_details/",
#         headers={"Authorization": f"Bearer {super_admin_token}"},
#         json=payload, params={"college_id": str(ObjectId())}
#     )
#     assert response.status_code == 404


# Test Case: Successfully Get Billing Details Without Filters
@pytest.mark.asyncio
async def test_get_billing_details_success_no_filters(http_client_test, super_admin_token, test_college_validation):
    """ Test Case: Successfully Get Billing Details Without Filters """
    payload = {"from_date": "2023-01-01", "to_date": "2025-04-01"}
    response = await http_client_test.post(
        f"/college/get_billing_details/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
        json=payload, params={"college_id": str(test_college_validation.get('_id'))}
    )
    assert response.status_code == 200


# Test Case: Successfully Get Billing Details With Filters
@pytest.mark.asyncio
async def test_get_billing_details_success_with_filters(http_client_test, super_admin_token, test_college_validation):
    """ Test Case: Successfully Get Billing Details With Filters """
    payload = {"filters": "last_30_days"}
    response = await http_client_test.post(
        f"/college/get_billing_details/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_token}"},
        json=payload, params={"college_id": str(test_college_validation.get('_id'))}
    )
    assert response.status_code == 200