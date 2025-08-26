"""
This file contains test cases related to create or update a script.
"""
import pytest
from bson import ObjectId
from datetime import datetime
from app.tests.conftest import user_feature_data

feature_key = user_feature_data()

@pytest.mark.asyncio
async def test_create_call_reviews_unauthenticated(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token, application_details
):
    # Un-authorized user tried to create call reviews.
    response = await http_client_test.post(
        f"/qa_manager/call_review/?feature_key={feature_key}"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_create_call_reviews_wrong_token(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token, application_details
):
    # Pass invalid access token for create review
    response = await http_client_test.post(
        f"/qa_manager/call_review/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer wrong"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}


@pytest.mark.asyncio
async def test_create_call_reviews_college_id_missing(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token, application_details
):
    # Required college id for create review
    response = await http_client_test.post(
        f"/qa_manager/call_review/?feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "College Id must be required and "
                                         "valid."}

@pytest.mark.asyncio
async def test_create_call_reviews_college_id_invalid(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token, application_details
):
    # Invalid college id for create review
    response = await http_client_test.post(
        f"/qa_manager/call_review/?college_id="
        f"1234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College id must be a 12-byte input "
                                         "or a 24-character hex string"}

@pytest.mark.asyncio
async def test_create_call_reviews_wrong_college_id(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token, application_details
):
    # Wrong college id for create reviews
    response = await http_client_test.post(
        f"/qa_manager/call_review/?college_id="
        f"123456789012345678901234&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
    )
    assert response.status_code == 422
    assert response.json() == {"detail": "College not found."}


@pytest.mark.asyncio
async def test_create_call_reviews_body_missing(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token, application_details
):
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().call_activity_collection.delete_many({})
    await DatabaseConfiguration().call_activity_collection.insert_one({
        "call_id": "96573201201709825297",
        "type": "Outbound",
        "call_from": ObjectId("62bfd13a5ce8a398ad101bd7"),
        "call_from_name": "viru chaudhary",
        "call_from_number": 9657320120,
        "call_to_number": 7416549874,
        "show_popup": False,
        "created_at": datetime.utcnow(),
        "application": ObjectId("65e0281146908328a6425eb4"),
        "call_to_name": "Telephony Testing",
        "call_to": ObjectId("65e0281146908328a6425eb3"),
        "duration": 34,
        "endtime": datetime.utcnow(),
        "mcube_file_path": "https:\\/\\/recordings.mcube.com\\/classic\\/2024\\/03\\/5138\\/outbound\\/96573201201709825297.wav",
        "pulse": "1",
        "ref_id": "",
        "starttime": datetime.utcnow(),
        "status": "Customer Busy"
    })
    calls = await DatabaseConfiguration().call_activity_collection.find_one({})
    
    # Required body for create a review
    response = await http_client_test.post(
        f"/qa_manager/call_review/?college_id="
        f"{str(test_college_validation.get('_id'))}&call_id="
        f"{str(calls.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_call_reviews_call_qc_status_missing(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token, application_details
):
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().call_activity_collection.delete_many({})
    await DatabaseConfiguration().call_activity_collection.insert_one({
        "call_id": "96573201201709825297",
        "type": "Outbound",
        "call_from": ObjectId("62bfd13a5ce8a398ad101bd7"),
        "call_from_name": "viru chaudhary",
        "call_from_number": 9657320120,
        "call_to_number": 7416549874,
        "show_popup": False,
        "created_at": datetime.utcnow(),
        "application": ObjectId("65e0281146908328a6425eb4"),
        "call_to_name": "Telephony Testing",
        "call_to": ObjectId("65e0281146908328a6425eb3"),
        "duration": 34,
        "endtime": datetime.utcnow(),
        "mcube_file_path": "https:\\/\\/recordings.mcube.com\\/classic\\/2024\\/03\\/5138\\/outbound\\/96573201201709825297.wav",
        "pulse": "1",
        "ref_id": "",
        "starttime": datetime.utcnow(),
        "status": "Customer Busy"
    })
    calls = await DatabaseConfiguration().call_activity_collection.find_one({})

    # qc status missing for create review
    response = await http_client_test.post(
        f"/qa_manager/call_review/?college_id="
        f"{str(test_college_validation.get('_id'))}&call_id="
        f"{str(calls.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={
            "product_knowledge": 34,
            "call_starting": 54,
            "call_closing": 98,
            "issue_handling": 65,
            "engagement": 88,
            "call_quality": 54,
            "remarks": "kdsfjk"
        }
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Qc Status must be required and valid."}


@pytest.mark.asyncio
async def test_create_call_reviews_call_invalid_qc_status(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token, application_details
):
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().call_activity_collection.delete_many({})
    await DatabaseConfiguration().call_activity_collection.insert_one({
        "call_id": "96573201201709825297",
        "type": "Outbound",
        "call_from": ObjectId("62bfd13a5ce8a398ad101bd7"),
        "call_from_name": "viru chaudhary",
        "call_from_number": 9657320120,
        "call_to_number": 7416549874,
        "show_popup": False,
        "created_at": datetime.utcnow(),
        "application": ObjectId("65e0281146908328a6425eb4"),
        "call_to_name": "Telephony Testing",
        "call_to": ObjectId("65e0281146908328a6425eb3"),
        "duration": 34,
        "endtime": datetime.utcnow(),
        "mcube_file_path": "https:\\/\\/recordings.mcube.com\\/classic\\/2024\\/03\\/5138\\/outbound\\/96573201201709825297.wav",
        "pulse": "1",
        "ref_id": "",
        "starttime": datetime.utcnow(),
        "status": "Customer Busy"
    })
    calls = await DatabaseConfiguration().call_activity_collection.find_one({})

    # invalid qc status for create review
    response = await http_client_test.post(
        f"/qa_manager/call_review/?college_id="
        f"{str(test_college_validation.get('_id'))}&call_id="
        f"{str(calls.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={
            "qc_status": "string",
            "product_knowledge": 0,
            "call_starting": 0,
            "call_closing": 0,
            "issue_handling": 0,
            "engagement": 0,
            "call_quality_score": 0,
            "remarks": "string"
        }
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "qc_status must be 'Accepted', 'Rejected' or 'Fatal Rejected'"}


@pytest.mark.asyncio
async def test_create_call_reviews_call_invalid_call_stating_field(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token, application_details
):
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().call_activity_collection.delete_many({})
    await DatabaseConfiguration().call_activity_collection.insert_one({
        "call_id": "96573201201709825297",
        "type": "Outbound",
        "call_from": ObjectId("62bfd13a5ce8a398ad101bd7"),
        "call_from_name": "viru chaudhary",
        "call_from_number": 9657320120,
        "call_to_number": 7416549874,
        "show_popup": False,
        "created_at": datetime.utcnow(),
        "application": ObjectId("65e0281146908328a6425eb4"),
        "call_to_name": "Telephony Testing",
        "call_to": ObjectId("65e0281146908328a6425eb3"),
        "duration": 34,
        "endtime": datetime.utcnow(),
        "mcube_file_path": "https:\\/\\/recordings.mcube.com\\/classic\\/2024\\/03\\/5138\\/outbound\\/96573201201709825297.wav",
        "pulse": "1",
        "ref_id": "",
        "starttime": datetime.utcnow(),
        "status": "Customer Busy"
    })
    calls = await DatabaseConfiguration().call_activity_collection.find_one({})

    # Invalid call starting value for create review
    response = await http_client_test.post(
        f"/qa_manager/call_review/?college_id="
        f"{str(test_college_validation.get('_id'))}&call_id="
        f"{str(calls.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={
            "qc_status": "Accepted",
            "product_knowledge": 0,
            "call_starting": 110,
            "call_closing": 0,
            "issue_handling": 0,
            "engagement": 0,
            "call_quality_score": 0,
            "remarks": "string"
        }
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "call_starting must be in between 0 and 10"}


@pytest.mark.asyncio
async def test_create_call_reviews_call_successfully(
    http_client_test, test_college_validation, setup_module,
    college_super_admin_access_token, application_details
):
    from app.database.configuration import DatabaseConfiguration
    await DatabaseConfiguration().call_activity_collection.delete_many({})
    await DatabaseConfiguration().call_activity_collection.insert_one({
        "call_id": "96573201201709825297",
        "type": "Outbound",
        "call_from": ObjectId("62bfd13a5ce8a398ad101bd7"),
        "call_from_name": "viru chaudhary",
        "call_from_number": 9657320120,
        "call_to_number": 7416549874,
        "show_popup": False,
        "created_at": datetime.utcnow(),
        "application": ObjectId("65e0281146908328a6425eb4"),
        "call_to_name": "Telephony Testing",
        "call_to": ObjectId("65e0281146908328a6425eb3"),
        "duration": 34,
        "endtime": datetime.utcnow(),
        "mcube_file_path": "https:\\/\\/recordings.mcube.com\\/classic\\/2024\\/03\\/5138\\/outbound\\/96573201201709825297.wav",
        "pulse": "1",
        "ref_id": "",
        "starttime": datetime.utcnow(),
        "status": "Customer Busy"
    })
    calls = await DatabaseConfiguration().call_activity_collection.find_one({})

    # Invalid call starting value for create review
    response = await http_client_test.post(
        f"/qa_manager/call_review/?college_id="
        f"{str(test_college_validation.get('_id'))}&call_id="
        f"{str(calls.get('_id'))}&feature_key={feature_key}",
        headers={"Authorization": f"Bearer "
                                  f"{college_super_admin_access_token}"},
        json={
            "qc_status": "Accepted",
            "product_knowledge": 8.0,
            "call_starting": 9.0,
            "call_closing": 2.0,
            "issue_handling": 2.0,
            "engagement": 1.0,
            "call_quality_score": 5.0,
            "remarks": "skdjfkjsdk"
        }
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Review added successfully."}
