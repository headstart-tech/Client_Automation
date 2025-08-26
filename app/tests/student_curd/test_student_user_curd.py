"""
This file contains test cases regarding student user curd API routes/endpoints
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_student_signup_country_code_not_found(
        http_client_test,
        setup_module,
        test_student_data,
        test_college_validation,
        test_counselor_validation):
    """
    Test case -> create student, when country_code not found
    :param http_client_test:
    :return:
    """

    test_student_data["email"] = "wrong@gmail.com"
    test_student_data["mobile_number"] = "2222222222"
    test_student_data["country_code"] = ""
    response = await http_client_test.post(
        f"/student_user_crud/signup?college_id={str(test_college_validation.get('_id'))}", json=test_student_data
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "Enter valid Country name."}

# TODO: The API got changed by Suphiya, need to update the test cases
# @pytest.mark.asyncio
# async def test_student_signup_country_code_must_be_required(http_client_test,
#                                                             setup_module,
#                                                             test_student_data,
#                                                             test_college_validation,
#                                                             test_counselor_validation):
#     """
#     Test case -> create student, when country_code is missing
#     :param http_client_test:
#     :return:
#     """
#     test_student_data.pop("country_code")
#     response = await http_client_test.post(
#         f"/student_user_crud/signup?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
#         json=test_student_data
#     )
#     assert response.status_code == 400
#     assert response.json() == {
#         "detail": "Country Code must be required and valid."}
#
#
# @pytest.mark.asyncio
# async def test_student_signup_state_name_not_found(http_client_test,
#                                                    setup_module,
#                                                    test_student_data,
#                                                    test_college_validation,
#                                                    test_counselor_validation):
#     """
#     Test case -> create student, when college id is invalid or not found
#     :param http_client_test:
#     :return:
#     """
#     test_student_data["email"] = "wrong@gmail.com"
#     test_student_data["mobile_number"] = "2222222222"
#     test_student_data["state_code"] = ""
#     response = await http_client_test.post(
#         f"/student_user_crud/signup?"
#         f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
#         json=test_student_data
#     )
#     assert response.status_code == 422
#     assert response.json() == {"detail": "Enter valid State name."}
#
#
# @pytest.mark.asyncio
# async def test_student_signup_state_code_must_be_required(http_client_test,
#                                                           setup_module,
#                                                           test_student_data,
#                                                    test_college_validation,
#                                                           test_counselor_validation):
#     """
#     Test case -> create student, when state_code is missing
#     :param http_client_test:
#     :return:
#     """
#     test_student_data.pop("state_code")
#     response = await http_client_test.post(
#         f"/student_user_crud/signup?college_id={str(test_college_validation.get('_id'))}"
#         f"&feature_key={feature_key}", json=test_student_data
#     )
#     assert response.status_code == 400
#     assert response.json() == {
#         "detail": "State Code must be required and valid."}
#
#
# @pytest.mark.asyncio
# async def test_student_signup_city_name_not_found(http_client_test,
#                                                   setup_module,
#                                                   test_student_data,
#                                                    test_college_validation,
#                                                   test_counselor_validation):
#     """
#     Test case -> create student, when city not found
#     :param http_client_test:
#     :return:
#     """
#     test_student_data["email"] = "wrong@gmail.com"
#     test_student_data["mobile_number"] = "2222222222"
#     test_student_data["city"] = ""
#     response = await http_client_test.post(
#         f"/student_user_crud/signup"
#         f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
#         json=test_student_data
#     )
#     assert response.status_code == 422
#     assert response.json() == {"detail": "city not found."}
#
#
# @pytest.mark.asyncio
# async def test_student_signup_city_must_be_required(http_client_test,
#                                                     setup_module,
#                                                     test_student_data,
#                                                    test_college_validation,
#                                                     test_counselor_validation):
#     """
#     Test case -> create student, when city is missing
#     :param http_client_test:
#     :return:
#     """
#     test_student_data["email"] = "wrong@gmail.com"
#     test_student_data.pop("city")
#     response = await http_client_test.post(
#         f"/student_user_crud/signup"
#         f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}", json=test_student_data
#     )
#     assert response.status_code == 400
#     assert response.json() == {"detail": "City must be required and valid."}
#
#
# @pytest.mark.asyncio
# async def test_student_signup_course_not_found(http_client_test, setup_module,
#                                                test_student_data,
#                                                    test_college_validation,
#                                                test_counselor_validation):
#     """
#     Test case -> create student when course not found in db
#     """
#     test_student_data["email"] = "wrong@gmail.com"
#     test_student_data["mobile_number"] = "2222222222"
#     test_student_data["course"] = ""
#     response = await http_client_test.post(
#         f"/student_user_crud/signup"
#         f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}", json=test_student_data
#     )
#     assert response.status_code == 404
#     assert response.json() == {'detail': 'course not found.'}
#
#
# @pytest.mark.asyncio
# async def test_student_signup_main_specialization_not_found(
#         http_client_test,
#         setup_module,
#         test_student_data,
#         test_college_validation,
#         test_counselor_validation):
#     """
#     Test case -> create student, when main specialization of course is not found
#     """
#     test_student_data["email"] = "wrong@gmail.com"
#     test_student_data["mobile_number"] = "2222222222"
#     test_student_data["main_specialization"] = ""
#     response = await http_client_test.post(
#         f"/student_user_crud/signup"
#         f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}", json=test_student_data
#     )
#     assert response.status_code == 404
#     assert response.json() == {
#         "detail": "main specialization not found in this course"}
#
#
# @pytest.mark.asyncio
# async def test_student_signup_college_id_not_found(http_client_test,
#                                                    setup_module,
#                                                    test_student_data,
#                                                    test_college_validation,
#                                                    test_counselor_validation):
#     """
#     Test case -> create student, when college id is invalid or not found
#     :param http_client_test:
#     :return:
#     """
#     test_student_data["email"] = "wrong@gmail.com"
#     test_student_data["mobile_number"] = "2222222222"
#     test_student_data["college_id"] = ""
#     response = await http_client_test.post(
#         f"/student_user_crud/signup"
#         f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}", json=test_student_data
#     )
#     assert response.status_code == 422
#     assert response.json() == {
#         "detail": "college_id must be a 12-byte input"
#                   " or a 24-character hex string"}
#
#
# @pytest.mark.asyncio
# async def test_student_signup_course_must_be_valid(http_client_test,
#                                                    setup_module,
#                                                    test_student_data,
#                                                    test_college_validation,
#                                                    test_counselor_validation):
#     """
#     Test case to create student when course name is invalid
#     """
#     test_student_data.pop("course")
#     response = await http_client_test.post(
#         f"/student_user_crud/signup"
#         f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}", json=test_student_data
#     )
#     assert response.status_code == 400
#     assert response.json() == {'detail': 'Course must be required and valid.'}
#
#
# @pytest.mark.asyncio
# async def test_student_signup(http_client_test, setup_module,
#                                                    test_college_validation,
#                               test_student_data):
#     """
#     Test case -> create student
#     :param http_client_test:
#     :return:
#     """
#     test_student_data["email"] = "wrong@gmail.com"
#     test_student_data["mobile_number"] = "2222222222"
#     response = await http_client_test.post(
#         f"/student_user_crud/signup"
#         f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
#         json=test_student_data
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Account Created Successfully."


@pytest.mark.asyncio
async def test_student_signup_with_extra_fields(http_client_test, setup_module,
                                                   test_college_validation,
                                                test_student_data):
    """
    Create student with extra fields
    """
    test_student_data.update({"email": "test@extrafields.com",
                              "extra_fields": {
                                  "education_qualification": "12th"},
                              "mobile_number": "5676776785"})
    response = await http_client_test.post(
        f"/student_user_crud/signup"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        json=test_student_data
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Account Created Successfully."


@pytest.mark.asyncio
async def test_student_signup_email_already_exists(http_client_test,
                                                   setup_module,
                                                   test_college_validation,
                                                   test_student_data):
    """
    Test case -> email already exists for create student
    :param http_client_test:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentsPrimaryDetails.delete_many({})
    test_student_data["email"] = "wrong@gmail.com"
    test_student_data["mobile_number"] = "2222222222"
    await http_client_test.post(
        f"/student_user_crud/signup?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}", json=test_student_data
    )
    response = await http_client_test.post(
        f"/student_user_crud/signup?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}", json=test_student_data
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Email already exists."


@pytest.mark.asyncio
async def test_student_signup_mobile_number_already_exists(http_client_test,
                                                           setup_module,
                                                   test_college_validation,
                                                           test_student_data):
    """
    Test case -> mobile number already exists for create student
    :param http_client_test:
    :return:
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().studentsPrimaryDetails.delete_many({})
    test_student_data["email"] = "wrong@gmail.com"
    test_student_data["mobile_number"] = "2222222222"
    await http_client_test.post(
        f"/student_user_crud/signup?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        json=test_student_data
    )
    test_student_data["email"] = "wronggg@gmail.com"
    response = await http_client_test.post(
        f"/student_user_crud/signup?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        json=test_student_data
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Mobile number already exists."


@pytest.mark.asyncio
async def test_logout_not_authenticated(http_client_test, setup_module):
    """
    Test case -> not authenticated if user not logged in
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(f"/student_user_crud/logout/?feature_key={feature_key}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_logout_bad_credentials(http_client_test, setup_module):
    """
    Test case -> bad token for student logout
    :param http_client_test:
    :return:
    """
    response = await http_client_test.get(
        f"/student_user_crud/logout/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_logout(http_client_test, access_token, setup_module, college_counselor_access_token):
    """
    Test case -> for successfully logout student
    :param http_client_test:
    :param access_token:
    :return:
    """
    response = await http_client_test.get(
        f"/student_user_crud/logout/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer {college_counselor_access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"success": "logout successfully"}


@pytest.mark.asyncio
async def test_update_student_primary_data_not_authenticated(
        http_client_test, test_college_validation, setup_module
):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.put(
        f"/student_user_crud/update_student_primary_data/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_student_primary_data_bad_credentials(
        http_client_test, test_college_validation, setup_module
):
    """
    Bad token for update student primary data
    """
    response = await http_client_test.put(
        f"/student_user_crud/update_student_primary_data/"
        f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

#
# @pytest.mark.asyncio
# async def test_update_student_primary_data(
#         http_client_test, test_college_validation, access_token, setup_module
# ):
#     """
#     Update student primary data
#     """
#     response = await http_client_test.put(
#         f"/student_user_crud/update_student_primary_data/"
#         f"?college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
#         headers={"Authorization": f"Bearer {access_token}"},
#         json={"alternate_number": 9999999999},
#     )
#     assert response.status_code == 200
#     assert response.json()['alternative_number'] == 9999999999


@pytest.mark.asyncio
async def test_verify_captcha(http_client_test, setup_module):
    """
    Test case -> for verify captcha
    :param http_client_test:
    :return:
    """
    response = await http_client_test.post(
        f"/student_user_crud/verify_captcha/?feature_key={feature_key}",
        json={
            "response": "03AGdBq2530mv32KRl9o4PlfTX-vKRdi3jHoIdPHSPIpKmNkBYemCewxAdgTMHiV1ZBRKlaCOYY6HTKcdYVB3B0Nh9z5xzCxV8I-XzgXq29Ei0cEVBZVf_PiETnEdLbtw0QFzTlnybiIzL2AIP9rzGkSpSIxPIMmhqcbXuOFHUWEjAiPklqYPUmXh1ODaKrb_2JW_cr98ItHPtoydsht2i78l1XEiw4nn1RSwtaGtMnTtmb87Z8rTWIyY1-dqe0gy1FjNY0prAQrRNS7TP2_uGq9BNhQx0hG8_-vurBWS0Ss2rc5-6VPdhHa1v_Y4NLATU8WxXddFTzgZkASY_ErdJJYfXBvck9dmwZzYwr-3DXJwTQ1V9mhzZMslboR6MWsYYon8uYHs6IXutC3XbKGIeKI-Ww0njiX8HNq1y_0pTB2cfEi4tevu1rbYpMafrio8Emeema29fmq_n"
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Bad request."

# Following test case execute only when we pass correct token response which we will get from frontend instead of 03AGdBq26wSW3_v_6rv2NL7Lt0UwfaXLCmBKm1HzrZh4_h9oAGnXdfAoK2_P9cWbnk9qscN7Ukr5ABGtTLqGg2e2OuO1zLVM8XNhbkhH_dGl8VHGzwx9Tp95fkKvSdRjQGOc_lHbWf1adoOYv_9ytBsRBgEh4OPQ7s03NTxJVWkUEGwl-PK1RS7mXo0duyahGvNb4PYPvT-2NRtfosiGRVdLtjCceoBkwo_oCYU7sll0TfrBEIdG8reibAhdjYhPzjA4aQwGePBSzk88wrKYjh2LMU_gZ6tlf8ymoqOYyM29enaZJ8ts08UON5eXo_FUPNULjwXyASc7eD4xe0OiVtav8DehfVbCANe1j2gzfYNgBCZp3UkOl-zwGzWT3JtgQ2lJjAa75pYEmPJSfh9lqQUFklRjweGQCz2iK5y1VtPsMQ1HzzxK4FVPxgHJ2ZRHzd0RsVaylL8wTi
# @pytest.mark.asyncio
# async def test_verify_captcha(http_client_test):
#     """
#     Test case -> for verify captcha
#     :param http_client_test:
#     :return:
#     """
#     response = await http_client_test.post("/student_user_crud/verify_captcha/", json={'response': '03AGdBq26wSW3_v_6rv2NL7Lt0UwfaXLCmBKm1HzrZh4_h9oAGnXdfAoK2_P9cWbnk9qscN7Ukr5ABGtTLqGg2e2OuO1zLVM8XNhbkhH_dGl8VHGzwx9Tp95fkKvSdRjQGOc_lHbWf1adoOYv_9ytBsRBgEh4OPQ7s03NTxJVWkUEGwl-PK1RS7mXo0duyahGvNb4PYPvT-2NRtfosiGRVdLtjCceoBkwo_oCYU7sll0TfrBEIdG8reibAhdjYhPzjA4aQwGePBSzk88wrKYjh2LMU_gZ6tlf8ymoqOYyM29enaZJ8ts08UON5eXo_FUPNULjwXyASc7eD4xe0OiVtav8DehfVbCANe1j2gzfYNgBCZp3UkOl-zwGzWT3JtgQ2lJjAa75pYEmPJSfh9lqQUFklRjweGQCz2iK5y1VtPsMQ1HzzxK4FVPxgHJ2ZRHzd0RsVaylL8wTi'})
#     assert response.status_code == 200
#     assert response.json()['message'] == 'Human is found.'
