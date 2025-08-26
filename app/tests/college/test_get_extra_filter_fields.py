"""
This file contains test cases related to get extra filter fields
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_extra_filter_fields_required_field(http_client_test, setup_module):
    """
    Required field for get extra filter fields
    """
    response = await http_client_test.get(f"/college/extra_filter_fields/?feature_key={feature_key}")
    assert response.status_code == 200
    assert response.json() == {'detail': "College not found. Make sure college_id or domain_url is correct."}


@pytest.mark.asyncio
async def test_get_extra_filter_fields_invalid_college_id(http_client_test):
    """
    Invalid college id for get extra filter fields
    """
    response = await http_client_test.get(
        f"/college/extra_filter_fields/?college_id=1234567890&feature_key={feature_key}")
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'


@pytest.mark.asyncio
async def test_get_extra_filter_fields_college_not_found(http_client_test):
    """
    College not found for get extra filter fields
    """
    response = await http_client_test.get(
        f"/college/extra_filter_fields/?college_id=123456789012345678901234&feature_key={feature_key}")
    assert response.status_code == 200
    assert response.json() == {'detail': "College not found. Make sure college_id or domain_url is correct."}


@pytest.mark.asyncio
async def test_get_extra_filter_fields_invalid_domain_url(
        http_client_test, access_token, setup_module, test_college_validation
):
    """
    Test case -> invalid domain url for get signup form extra fields
    """
    response = await http_client_test.get(
        f"/college/extra_filter_fields/?domain_url=https://test.com&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response.json() == {'detail': "College not found. Make sure college_id or domain_url is correct."}


@pytest.mark.asyncio
async def test_get_extra_filter_fields(
        http_client_test, super_admin_access_token, setup_module, test_college_validation
):
    """
    Test case -> Get extra filter fields
    """
    fields = ["extra_field", "field_type"]
    from app.database.configuration import DatabaseConfiguration

    await DatabaseConfiguration().college_form_details.update_one(
        {"college_id": test_college_validation.get('_id')},
        {'$unset': {
            'form_details.student_registration_form_fields': True
        }},
    )
    await DatabaseConfiguration().college_collection.update_one(
        {"_id": test_college_validation.get('_id')},
        {'$unset': {
            "dashboard_domain": True
        }}
    )
    # Extra filter fields not found by college_id
    response = await http_client_test.get(
        f"/college/extra_filter_fields/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get extra filter fields."
    assert response.json()['data'] == []

    # Extra filter fields not found by domain url
    response = await http_client_test.get(
        f"/college/extra_filter_fields/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get extra filter fields."
    assert response.json()['data'] == []

    await DatabaseConfiguration().college_form_details.update_one(
        {"college_id": test_college_validation.get('_id')},
        {'$set': {
            'form_details.student_registration_form_fields': [
                {
                    "field_name": "Test", "field_type": "select",
                    "is_mandatory": True, "editable": False,
                    "can_remove": False, "extra_field": True
                }
            ]
        }},
        upsert=True
    )
    await DatabaseConfiguration().college_collection.update_one(
        {"_id": test_college_validation.get('_id')},
        {'$set': {
            "dashboard_domain": "https://test.com"
        }}
    )
    # Get extra filter fields by college_id
    response = await http_client_test.get(
        f"/college/extra_filter_fields/?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get extra filter fields."
    assert response.json()['data'] != []
    for field in fields:
        assert field in response.json()["data"][0]

    # Get extra filter fields found by domain url
    response = await http_client_test.get(
        f"/college/extra_filter_fields/?domain_url=https://test.com&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {super_admin_access_token}"}
    )
    assert response.status_code == 200
    assert response.json()['message'] == "Get extra filter fields."
    assert response.json()['data'] != []
    for field in fields:
        assert field in response.json()["data"][0]
