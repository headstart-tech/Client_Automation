"""
This file contains test cases to get applied students of promocode
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_get_applied_students(http_client_test, test_college_validation, setup_module, test_promocode,
                                                      college_super_admin_access_token):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_applied_students/?college_id={str(test_college_validation.get('_id'))}"
        f"&promocode_id={str(test_promocode.get('_id'))}&page_num=1&page_size=1&feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    """
    Bad token to get applied students
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_applied_students/?college_id={str(test_college_validation.get('_id'))}"
        f"&promocode_id={str(test_promocode.get('_id'))}&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

    """
    promocode id required to get applied students
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_applied_students/?college_id={str(test_college_validation.get('_id'))}"
        f"&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Promocode Id must be required and valid."}

    """
    Required college id to get applied students
    """
    response = await http_client_test.post(f"/promocode_vouchers/get_applied_students/"
                                           f"?promocode_id={str(test_promocode.get('_id'))}&page_num=1&page_size=1"
                                           f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'College Id must be required and valid.'

    """
    Invalid college id to get applied students
    """
    response = await http_client_test.post(f"/promocode_vouchers/get_applied_students/?college_id=1234567890"
                                           f"&promocode_id={str(test_promocode.get('_id'))}&page_num=1&page_size=1"
                                           f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College id must be a 12-byte input or a 24-character hex string'

    """
    College not found to get applied students
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_applied_students/?college_id=123456789012345678901234&"
        f"promocode_id={str(test_promocode.get('_id'))}&page_name=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json()['detail'] == 'College not found.'

    """
    Required college id to get student details
    """
    response = await http_client_test.post(f"/promocode_vouchers/get_applied_students/"
                                           f"?college_id={str(test_college_validation.get('_id'))}&page_num=1"
                                           f"&page_size=1&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Promocode Id must be required and valid.'

    """
    Required page num to get students applied
    """
    response = await http_client_test.post(f"/promocode_vouchers/get_applied_students/"
                                           f"?college_id={str(test_college_validation.get('_id'))}"
                                           f"&promocode_id={str(test_promocode.get('_id'))}&page_size=1"
                                           f"&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Page Num must be required and valid.'

    """
    Required page size to get students applied
    """
    response = await http_client_test.post(f"/promocode_vouchers/get_applied_students/"
                                           f"?college_id={str(test_college_validation.get('_id'))}&page_num=1&"
                                           f"promocode_id={str(test_promocode.get('_id'))}&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 400
    assert response.json()['detail'] == 'Page Size must be required and valid.'

    """
    Invalid promocode id to get applied students
    """
    response = await http_client_test.post(f"/promocode_vouchers/get_applied_students/"
                                           f"?college_id={str(test_college_validation.get('_id'))}&promocode_id=123456"
                                           f"&page_num=1&page_size=1&feature_key={feature_key}",
                                           headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
                                           )
    assert response.status_code == 422
    assert response.json()['detail'] == 'Promocode id must be a 12-byte input or a 24-character hex string'

    """
    promocode not found to get applied students
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_applied_students/?college_id={str(test_college_validation.get('_id'))}"
        f"&promocode_id=123456789012345678901234&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
    )
    assert response.status_code == 404
    assert response.json()['detail'] == 'Promocode not found id: 123456789012345678901234'

    """
    get applied students
    """
    response = await http_client_test.post(
        f"/promocode_vouchers/get_applied_students/?college_id={str(test_college_validation.get('_id'))}"
        f"&promocode_id={str(test_promocode.get('_id'))}&page_num=1&page_size=1&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_super_admin_access_token}"},
        json= {"units": 20}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Get applied students info"
