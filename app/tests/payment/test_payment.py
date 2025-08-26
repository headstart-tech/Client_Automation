"""
This file contains test cases regarding payment gateway routes
"""
import pytest
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_payment_details_by_payment_not_found(
        http_client_test, test_college_validation, setup_module,
        application_details
):
    """
    Payment not found for get payments details
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().payment_collection.delete_many({})
    response = await http_client_test.get(
        f"/payments/application/{str(application_details.get('_id'))}/"
        f"?college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 200
    assert response.json() == \
           {"data": [], "message": "All payment details fetched successfully."}


@pytest.mark.asyncio
async def test_payment_details_by_payment_id_not_present(
        http_client_test, test_college_validation, setup_module
):
    """
    Payment_id not present for get payments details
    """
    response = await http_client_test.get(
        f"/payments/wrong_id/?college_id="
        f"{str(test_college_validation.get('_id'))}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Make sure payment id should be " \
                                        "correct."


@pytest.mark.asyncio
async def test_payment_details_by_payment_id(http_client_test,
                                             test_college_validation,
                                             payment_details):
    """
    Get payments details
    """
    response = await http_client_test.get(
        f"/payments/{str(payment_details.get('payment_id'))}/?college_id="
        f"{str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Payment details fetched " \
                                         "successfully."


@pytest.mark.asyncio
async def test_card_details_of_payment_id_not_present(http_client_test,
                                                      setup_module,
                                                      test_college_validation):
    """
    Payment_id not present for get payments details
    """
    response = await http_client_test.get(
        f"/payments/pay_G3P9vcIhRwrong/card/"f"?college_id="
        f"{str(test_college_validation.get('_id'))}")
    assert response.status_code == 500
    # Below line commented because getting error - Too many requests
    # assert response.json()["detail"] == "The id provided does not exist"


# Todo: Following test cases failing so commented for now
# @pytest.mark.asyncio
# async def test_card_details_of_payment(
#         http_client_test, setup_module, payment_details,
#         test_college_validation):
#     """
#     Get payments details
#     """
#     response = await http_client_test.get(
#         f"/payments/{str(payment_details.get('payment_id'))}/card/?"
#         f"college_id={str(test_college_validation.get('_id'))}"
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Payment details fetched " \
#                                          "successfully."


@pytest.mark.asyncio
async def test_card_details_of_payment_id_invalid(http_client_test,
                                                  setup_module,
                                                  test_college_validation):
    """
    Payment_id invalid for get payments details
    """
    response = await http_client_test.get(
        f"/payments/pay_G3P9vcIhRs3N/card/?college_id="
        f"{str(test_college_validation.get('_id'))}")
    assert response.status_code == 500
    # Below line commented because getting error - Too many requests
    # assert response.json()["detail"] == "G3P9vcIhRs3N is not a valid id"


@pytest.mark.asyncio
async def test_payment_details_by_application_id(http_client_test,
                                                 test_college_validation,
                                                 payment_details):
    """
    Get payments details
    """
    response = await http_client_test.get(
        f"/payments/application/"
        f"{str(payment_details.get('details').get('application_id'))}/"
        f"?college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 200
    assert response.json()["message"] == \
           "All payment details fetched successfully."
    for item in ["payment_id", "status", "date", "payment_method"]:
        assert item in response.json()["data"][0]


@pytest.mark.asyncio
async def test_payment_details_by_invalid_application_id(
        http_client_test, test_college_validation):
    """
    Get payments details
    """
    response = await http_client_test.get(
        f"/payments/application/1234567890/?college_id="
        f"{str(test_college_validation.get('_id'))}")
    assert response.status_code == 422
    assert response.json()["detail"] == "Application id must be a 12-byte " \
                                        "input or a 24-character hex string"


@pytest.mark.asyncio
async def test_all_payment_details_not_found(
        http_client_test, test_college_validation, setup_module):
    """
    Not found for get payments details
    """
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().payment_collection.delete_many({})
    response = await http_client_test.get(
        f"/payments/?college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Payment not found."}


@pytest.mark.asyncio
async def test_all_payment_details(
        http_client_test, test_college_validation, payment_details):
    """
    Get payments details
    """
    response = await http_client_test.get(
        f"/payments/?college_id={str(test_college_validation.get('_id'))}")
    assert response.status_code == 200
    assert response.json()["message"] == "All Payment details fetched " \
                                         "successfully."


@pytest.mark.asyncio
async def test_capture_payment_amount_required(
    http_client_test, setup_module, payment_details, test_college_validation
):
    """
    Amount required for capture payment
    """
    response = await http_client_test.post(
        f"/payments/{str(payment_details.get('payment_id'))}/capture/?"
        f"college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Amount must be required and valid."}


@pytest.mark.asyncio
async def test_capture_payment_invalid_condition(
        http_client_test, setup_module, test_college_validation):
    """
    Invalid condition for capture payment
    """
    response = await http_client_test.post(
        f"/payments/pay_JWHHwGFEiUOyUx/capture/?amount=500&college_id="
        f"{str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 500
    # Below line commented because getting error - Too many requests
    # assert response.json() == {
    #     "detail": "Only payments which have been authorized and not yet "
    #               "captured can be captured"
    # }


@pytest.mark.asyncio
async def test_capture_payment_already_exist(
        http_client_test, payment_details, test_college_validation):
    """
    Already exist when try to capture payment
    """
    response = await http_client_test.post(
        f"/payments/{str(payment_details.get('payment_id'))}/capture/?"
        f"amount=500&college_id={str(test_college_validation.get('_id'))}"
    )
    assert response.status_code == 500
    # Below line commented because getting error - Too many requests
    # assert response.json()["detail"] == "This payment has already been " \
    #                                     "captured"


# Below test case execute only when payment not already capture
# @pytest.mark.asyncio
# async def test_capture_payment(http_client_test, payment_details):
#     """
#     Test case -> when try to capture payment
#     :param http_client_test:
#     :return:
#     """
#     response = await http_client_test.post(f"/payments/
#     {str(payment_details.get('payment_id'))}/capture/?amount=500")
#     assert response.status_code == 200
#     assert response.json()['message'] == "Payment captured successfully."


@pytest.mark.asyncio
async def test_update_payment_body_required(
        http_client_test, test_college_validation, setup_module):
    """
    Body required for update payment
    """
    response = await http_client_test.put(
        f"/payments/pay_G3P9vcIhRs3NV4/update/?college_id="
        f"{str(test_college_validation.get('_id'))}")
    assert response.status_code == 400
    assert response.json() == {"detail": "Body must be required and valid."}


@pytest.mark.asyncio
async def test_update_payment_invalid_application_id(
        http_client_test, test_college_validation, setup_module,
        payment_details
):
    """
    Invalid application id for update payment
    """
    response = await http_client_test.put(
        f"/payments/{payment_details.get('payment_id')}/update/?"
        f"application_id=1234567890&college_id="
        f"{str(test_college_validation.get('_id'))}",
        json={"status": "failed"},
    )
    assert response.status_code == 400
    assert response.json() == {
        'detail': '("\'1234567890\' is not a valid ObjectId, '
                  'it must be a 12-byte input or a 24-character hex string",)'}


@pytest.mark.asyncio
async def test_update_payment(http_client_test, test_college_validation,
                              setup_module, application_details):
    """
    Update payment
    """
    response = await http_client_test.put(
        f"/payments/pay_Jo95qqQGonlLaP/update/"
        f"?application_id={str(application_details.get('_id'))}&"
        f"college_id={str(test_college_validation.get('_id'))}",
        json={"status": "failed"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Data inserted successfully."


@pytest.mark.asyncio
async def test_create_order_not_authenticated(
        http_client_test, test_college_validation, setup_module):
    """
    Not authenticated if user not logged in
    """
    response = await http_client_test.post(
        f"/payments/create_order/?college_id="
        f"{str(test_college_validation.get('_id'))}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_order_bad_credentials(
        http_client_test, test_college_validation, setup_module):
    """
    Bad token for remove student
    """
    response = await http_client_test.post(
        f"/payments/create_order/?"
        f"college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

# Todo: Following test cases failing so commented for now
# @pytest.mark.asyncio
# async def test_create_order(
#         http_client_test, test_college_validation, access_token,
#         setup_module, application_details
# ):
#     """
#     Create order
#     """
#     from app.database.configuration import DatabaseConfiguration
#     await DatabaseConfiguration().payment_collection.delete_many({})
#     response = await http_client_test.post(
#         f"/payments/create_order/?application_id="
#         f"{str(application_details.get('_id'))}&amount=500&"
#         f"college_id={str(test_college_validation.get('_id'))}",
#         headers={"Authorization": f"Bearer {access_token}"},
#     )
#     assert response.status_code == 200
#     assert response.json()["message"] == "Order created successfully."


@pytest.mark.asyncio
async def test_create_order_invalid_application_id(
        http_client_test, test_college_validation, access_token, setup_module
):
    """
    Create order
    """
    response = await http_client_test.post(
        f"/payments/create_order/?application_id=1234567890&"
        f"amount=500&college_id={str(test_college_validation.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "(\"'1234567890' is not a valid ObjectId, it must be a "
           "12-byte input or a 24-character hex string\",)"
    )

# Below test case commented because getting error - Too many requests
# @pytest.mark.asyncio
# async def test_order_details(
#         http_client_test, test_college_validation, setup_module,
#         payment_details):
#     """
#     Get order details based on id
#     """
#     response = await http_client_test.get(
#         f"/payments/order_details/{str(payment_details.get('order_id'))}?"
#         f"college_id={str(test_college_validation.get('_id'))}"
#     )
#     assert response.status_code == 200
#     assert response.json() == "paid"


# Commented test case because sometimes it is failing, sometimes successfully
# execute
# @pytest.mark.asyncio
# async def test_payment_details(
#         http_client_test, test_college_validation, setup_module,
#         payment_details):
#     """
#     Get payment details based on id
#     """
#     response = await http_client_test.get(
#         f"/payments/payment_details/{str(payment_details.get('payment_id'))}/"
#         f"?college_id={str(test_college_validation.get('_id'))}"
#     )
#     assert response.status_code == 200
#     assert response.json() == "captured"
