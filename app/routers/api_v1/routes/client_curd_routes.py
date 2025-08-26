"""
This File Contains the CRUD Routes for the Client, It can be Used by Higher Hierarchies
"""
from fastapi import APIRouter, Query, Path, HTTPException
from app.core.log_config import get_logger
from app.models.client_schema import (
    ClientModel,
    ClientConfigurationModel,
    ClientUpdateModel,
    ClientDetailsResponse
)
from app.helpers.client_curd.client_curd_helper import ClientCurdHelper
from app.core.utils import utility_obj, requires_feature_permission
from app.dependencies.oauth import CurrentUser
from app.helpers.user_curd.user_configuration import UserHelper
from typing import Annotated, Optional
from app.core.custom_error import CustomError, DataNotFoundError

logger = get_logger(__name__)
client_crud_router = APIRouter()

@client_crud_router.post('/create/')
@requires_feature_permission("write")
async def create_client(request: ClientModel, current_user: CurrentUser):
    """
    Creates a new client with associated configurations.

    ### Request Body:
    - **client_name** (str): Name of the client (e.g., "Delta University").
    - **client_email** (str): Client's email address.
     - **client_phone** (str): Client's phone number.
    - **assigned_account_managers** (List[str]): List of assigned manager IDs.
    - **address** (dict): Address details of the client.
      - **address_line_1** (str): Primary address line.
      - **address_line_2** (str): Secondary address line.
      - **city_name** (str): City name.
      - **state_code** (str): State code.
      - **country_code** (str): Country code.
    - **websiteUrl** (str): Client's website URL.
    - **POCs** (List[dict]): List of Points of Contact.
      - **name** (str): Name of the contact person.
      - **email** (str): Email of the contact person.
      - **mobile_number** (str): Mobile number of the contact person.

    ### Example Body:
    ```json
    {
       "client_name":"Delta University",
       "client_email":"randomuser245@yopmail.com",
       "client_phone":"9876543210",
       "assigned_account_managers":[
          "6643a5874b12e3fc9c7f12ab",
          "6643a5874b12e3fc9c7f12bc",
          "6643a5874b12e3fc9c7f12cd"
       ],
       "address":{
          "address_line_2":"Tech Park, Sector 21",
          "address_line_1":"Building 5, Level 3",
          "city_name":"Pune",
          "state_code":"MH",
          "country_code":"IN"
       },
       "websiteUrl":"https://dev3.university.edu/",
       "POCs":[
          {
             "name":"John Doe",
             "email":"johndoe123@university.edu",
             "mobile_number":"9876543210"
          },
          {
             "name":"Jane Smith",
             "email":"janesmith@university.edu",
             "mobile_number":"9123456789"
          },
          {
             "name":"Robert Johnson",
             "email":"robert.johnson@university.edu",
             "mobile_number":"9012345678"
          }
       ]
    }
    ```

    ### Response Body:
    - **data** (List[dict]): Contains details about the created client.
      - **client_id** (str): Unique identifier of the created client.
      - **document_id** (str): Unique document ID associated with the client.
    - **code** (int): HTTP status code (200 on success).
    - **message** (str): Response message ("Client Created Successfully").
    """
    # TODO AUTHENTICATE & CHECK PERMISSION THROUGH WITH NEW RBAC SYSTEM
    try:
        user = await UserHelper().is_valid_user(current_user)
        data = await ClientCurdHelper().create_client(request.model_dump(), user)
        return utility_obj.response_model(data, "Client Created Successfully")
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@client_crud_router.post('/{client_id}/configuration/add')
@requires_feature_permission("write")
async def add_client_configuration(
        client_id: Annotated[str, Path(title="Client ID", description="Object ID of the client")],
        request: ClientConfigurationModel,
        current_user: CurrentUser
):
    """
        Adds configuration details for a client.

        ### Path Parameter:
        - **client_id** (str): Object ID of the client.

        ### Request Body:
        - **s3** (dict): AWS S3 storage configuration.
          - **username** (str): S3 username.
          - **aws_access_key_id** (str): AWS access key ID.
          - **aws_secret_access_key** (str): AWS secret access key.
          - **region_name** (str): AWS region.
          - **assets_bucket_name** (str): Bucket name for assets.
          - **reports_bucket_name** (str): Bucket name for reports.
          - **public_bucket_name** (str): Public-facing bucket name.
          - **student_documents_name** (str): Bucket name for student documents.
          - **report_folder_name** (str): Folder name for reports.
          - **download_bucket_name** (str): Bucket for downloads.
          - **demo_base_bucket_url** (str): Base URL for demo environment.
          - **dev_base_bucket_url** (str): Base URL for development environment.
          - **prod_base_bucket_url** (str): Base URL for production environment.
          - **stage_base_bucket_url** (str): Base URL for staging environment.
          - **demo_base_bucket** (str): Bucket name for demo environment.
          - **dev_base_bucket** (str): Bucket name for development environment.
          - **prod_base_bucket** (str): Bucket name for production environment.
          - **stage_base_bucket** (str): Bucket name for staging environment.
          - **base_folder** (str): Base folder for client-related storage.
        - **collpoll** (dict): CollPoll API integration details.
          - **aws_access_key_id** (str): AWS access key ID.
          - **aws_secret_access_key** (str): AWS secret access key.
          - **region_name** (str): AWS region for CollPoll.
          - **s3_bucket_name** (str): CollPoll S3 bucket.
          - **collpoll_url** (str): API URL for CollPoll integration.
          - **collpoll_auth_security_key** (str): Authorization key for CollPoll API.
        - **sms** (dict): SMS service configuration.
          - **username_trans** (str): Username for transactional messages.
          - **username_pro** (str): Username for promotional messages.
          - **password** (str): Password for SMS API.
          - **authorization** (str): Authorization token.
          - **sms_send_to_prefix** (str): Country code prefix for SMS.
        - **meilisearch** (dict): Meilisearch configuration.
          - **meili_server_host** (str): MeiliSearch server URL.
          - **meili_server_master_key** (str): Master key for MeiliSearch.
        - **report_webhook_api_key** (str): API key for report webhook.
        - **aws_textract** (dict): AWS Textract configuration.
          - **textract_aws_access_key_id** (str): AWS access key ID.
          - **textract_aws_secret_access_key** (str): AWS secret access key.
          - **textract_aws_region_name** (str): AWS region for Textract.
        - **whatsapp_credential** (dict): WhatsApp API credentials.
          - **send_whatsapp_url** (str): API URL for sending messages.
          - **generate_whatsapp_token** (str): API URL for generating authentication token.
          - **whatsapp_username** (str): Username for WhatsApp API.
          - **whatsapp_password** (str): Password for WhatsApp API.
          - **whatsapp_sender** (str): Sender ID for WhatsApp messages.
        - **cache_redis** (dict): Redis caching configuration.
          - **host** (str): Redis server host.
          - **port** (int): Redis port.
          - **password** (str): Redis authentication password.
        - **tawk_secret** (str): Secret key for Tawk.to integration.
        - **telephony_secret** (str): Secret key for telephony services.
        - **razorpay** (dict): Razorpay payment gateway configuration.
          - **razorpay_api_key** (str): API key for Razorpay.
          - **razorpay_secret** (str): API secret for Razorpay.
          - **razorpay_webhook_secret** (str): Webhook secret for Razorpay.
          - **partner** (bool): Indicates if the client is a Razorpay partner.
          - **x_razorpay_account** (str): Razorpay account ID.
        - **rabbit_mq_credential** (dict): RabbitMQ message broker configuration.
          - **rmq_host** (str): RabbitMQ host.
          - **rmq_password** (str): RabbitMQ authentication password.
          - **rmq_url** (str): RabbitMQ server URL.
          - **rmq_username** (str): RabbitMQ username.
          - **rmq_port** (str): RabbitMQ port.
        - **zoom_credentials** (dict): Zoom API credentials.
          - **client_id** (str): Client ID for Zoom.
          - **client_secret** (str): Client secret for Zoom.
          - **account_id** (str): Account ID for Zoom.

        ### Example Body:
        ```json
    {
       "s3":{
          "username":"dummy_s3_user",
          "aws_access_key_id":"DUMMY_AWS_ACCESS_KEY_ID_XXXXXXXX",
          "aws_secret_access_key":"DUMMY_AWS_SECRET_ACCESS_KEY_xxxxxxxxxxxxxxxxxx",
          "region_name":"us-east-1",
          "assets_bucket_name":"dummy-assets-bucket-sb",
          "reports_bucket_name":"dummy-reports-bucket-sb",
          "public_bucket_name":"dummy-public-bucket-sb",
          "student_documents_name":"dummy-student-docs-sb",
          "report_folder_name":"ReportsDummyApp",
          "download_bucket_name":"dummy-downloads",
          "demo_base_bucket_url":"https://dummy-demo-sb.s3.amazonaws.com/",
          "dev_base_bucket_url":"https://dummy-dev-sb.s3.amazonaws.com/",
          "prod_base_bucket_url":"https://dummy-prod-sb.s3.amazonaws.com/",
          "stage_base_bucket_url":"https://dummy-stage-sb.s3.amazonaws.com/",
          "demo_base_bucket":"dummy-demo-sb",
          "dev_base_bucket":"dummy-dev-sb",
          "prod_base_bucket":"dummy-prod-sb",
          "stage_base_bucket":"dummy-stage-sb"
       },
       "collpoll":{
          "aws_access_key_id":"DUMMY_COLLPOLL_AWS_KEY_ID_XXXX",
          "aws_secret_access_key":"DUMMY_COLLPOLL_AWS_SECRET_KEY_xxxxxxxxxxxx",
          "region_name":"us-west-2",
          "s3_bucket_name":"dummy.collpoll.bucket",
          "collpoll_url":"https://dummyuniversity.collpoll-api.com/rest/integration/users/prospectiveStudents",
          "collpoll_auth_security_key":"Basic DUMMY_COLLPOLL_AUTH_KEY_xxxxxxxxxxxx"
       },
       "sms":{
          "username_trans":"dummy_sms_user.trans",
          "username_pro":"dummy_sms_user.pro",
          "password":"DummySmsPassword",
          "authorization":"Basic DUMMYBASE64ENCODEDAUTHSTRING",
          "sms_send_to_prefix":"91"
       },
       "meilisearch":{
          "meili_server_host":"http://dummy.meilisearch.example.com:7700/",
          "meili_server_master_key":"DUMMY_MEILI_MASTER_KEY_XXXXXXXXXXXXXXXXXXXX"
       },
       "aws_textract":{
          "textract_aws_access_key_id":"DUMMY_TEXTRACT_AWS_KEY_ID_XXXX",
          "textract_aws_secret_access_key":"DUMMY_TEXTRACT_AWS_SECRET_KEY_xxxxxxxxxxxx",
          "textract_aws_region_name":"ap-south-1"
       },
       "whatsapp_credential":{
          "send_whatsapp_url":"https://api.dummywhatsappprovider.com/psms/servlet/psms.JsonEservice",
          "generate_whatsapp_token":"https://api.dummywhatsappprovider.com/psms/api/messages/token?action=generate",
          "whatsapp_username":"dummy_whatsapp_user",
          "whatsapp_password":"DummyWhatsappPassword123!",
          "whatsapp_sender":"910000000000"
       },
       "rabbit_mq_credential":{
          "rmq_host":"dummy_vhost",
          "rmq_password":"DummyRmqPassword!@#",
          "rmq_url":"rabbitmq.dummy-server.com",
          "rmq_username":"dummy_rmq_user",
          "rmq_port":"5672"
       },
       "zoom_credentials":{
          "client_id":"DUMMY_ZOOM_CLIENT_ID_xxxxxx",
          "client_secret":"DUMMY_ZOOM_CLIENT_SECRET_xxxxxx",
          "account_id":"DUMMY_ZOOM_ACCOUNT_ID_xxxxxx"
       }
    }
    ```

        ### Response Body:
         - **message** (str): Response message ("Client Configuration Added Successfully").
    """
    # TODO AUTHENTICATE & CHECK PERMISSION THROUGH WITH NEW RBAC SYSTEM
    try:
        user = await UserHelper().is_valid_user(current_user)
        data = await ClientCurdHelper().add_client_configuration(client_id, request.model_dump(), user)
        return data
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))

@client_crud_router.get('/{client_id}/configuration/get')
@requires_feature_permission("read")
async def get_client_configuration(
        current_user: CurrentUser,
        client_id: Annotated[str, Path(title="Client ID", description="Object ID of the client")],
    ):
    """
    Retrieves configuration details for a client.

    ### Path Parameter:
    - **client_id** (str): Object ID of the client.

    ### Response Body:
    - **data** (dict): Contains configuration details for the client.
    - **message** (str): Response message ("Client Configuration Found").
    """
    # TODO AUTHENTICATE & CHECK PERMISSION THROUGH WITH NEW RBAC SYSTEM
    try:
        await UserHelper().is_valid_user(current_user)
        data = await ClientCurdHelper().get_client_configuration(client_id)
        data.update({"message": "Client Configuration Found"})
        return data
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))

@client_crud_router.get('/{client_id}/', response_model=ClientDetailsResponse)
@requires_feature_permission("read")
async def get_client(
    client_id: Annotated[
      str, Path(title="Client ID", description="Object ID of the client")
    ],
    current_user: CurrentUser
):
    """
    Retrieves details of a specific client.

    ### Path Parameter:
    - **client_id** (str): Object Id of the client.

    ### Response Body:
    - _id (str): Unique identifier for the client.
    - client_name (str): Name of the client organization.
    - client_email (str): Email address associated with the client.
    - client_phone (str): Phone Number associated with the client.
    - assigned_manager (list[str]): List of assigned manager IDs.
    - student_dashboard_form (str): ID referencing the student dashboard form.
    - student_dashboard_screen (str): ID referencing the student dashboard screen.
    - admin_dashboard_screen (str): ID referencing the admin dashboard screen.
    - address (dict): Address details of the client.
        - address_line_1 (str): First line of the address.
        - address_line_2 (str): Second line of the address.
        - city_name (str): City name.
        - state (str): State name.
        - country (str): Country name.
    - websiteUrl (str): Client's website URL.
    - POCs (list[dict]): List of Points of Contact (POCs).
        - name (str): Name of the contact person.
        - email (str): Email address of the contact person.
        - mobile_number (str): Mobile number of the contact person.
    - created_by (str): ID of the user who created this client entry.
    - created_at (str): Timestamp when the client entry was created.
    - updated_at (str): Timestamp when the client entry was last updated.
    - statusInfo (dict): Activation status information.
        - isActivated (bool): Whether the client is activated.
        - activationDate (str): Activation date.
        - deActivationDate (str or None): Deactivation date (if applicable).
    """
    # TODO AUTHENTICATE & CHECK PERMISSION THROUGH WITH NEW RBAC SYSTEM
    try:
        user = await UserHelper().is_valid_user(current_user)
        data = await ClientCurdHelper().get_client(client_id, user)
        return data
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@client_crud_router.get('/all')
@requires_feature_permission("read")
async def get_all_clients(
    current_user: CurrentUser,
    page: Optional[int] = Query(None, gt=0),
    limit: Optional[int] = Query(None, gt=0),
):
    """
    Retrieves details of all clients.

    ### Query Parameters:
    - **page** (int): Page number for pagination.
    - **limit** (int): Number of records per page.

    ### Response Body:
    - **data** (List[dict]): Contains details about the clients.
    - **message** (str): Response message ("Client Data List Found").
    """
    # TODO AUTHENTICATE & CHECK PERMISSION THROUGH WITH NEW RBAC SYSTEM
    try:
        user = await UserHelper().is_valid_user(current_user)
        data = await ClientCurdHelper().get_all_clients(
            user=user, page=page, limit=limit, route="/client/all"
        )
        return data
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))

@client_crud_router.put('/{client_id}/update')
@requires_feature_permission("edit")
async def update_client(
        client_id: Annotated[
            str, Path(title="Client ID", description="Object ID of the client")
        ],
        request: ClientUpdateModel,
        current_user: CurrentUser
    ):
    """
    Updates details of a specific client.

    ### Path Parameter:
    - **client_id** (str): Object ID of the client.

    ### Request Body:
    - **client_name** (str): Name of the client (e.g., "Delta University").
    - **client_email** (str): Client's email address.
    - **client_phone** (str): Client's phone number.
    - **address** (dict): Address details of the client.
      - **address_line_1** (str): Primary address line.
      - **address_line_2** (str): Secondary address line.
      - **city_name** (str): City name.
      - **state_code** (str): State code.
      - **country_code** (str): Country code.
    - **websiteUrl** (str): Client's website URL.
    - **POCs** (List[dict]): List of Points of Contact.
      - **name** (str): Name of the contact person.
      - **email** (str): Email of the contact person.
      - **mobile_number** (str): Mobile number of the contact person.

    ### Example Body:
    ```json
    {
       "client_email":"randomemail@random.com",
       "address":{
          "address_line_2":"T-51",
          "address_line_1":"Sector 8",
          "city_name":"Noida",
          "state_code":"UP",
          "country_code":"IN"
       },
       "POCs": [
           {
              "name": "John Doe",
              "email": "randomemail@random.com",
              "mobile_number": "1234567890"
           }
       ]
    }
    ```

    ### Response Body:
    - **message** (str): Response message ("Client Updated Successfully").
    """
    # TODO AUTHENTICATE & CHECK PERMISSION THROUGH WITH NEW RBAC SYSTEM
    try:
        await UserHelper().is_valid_user(current_user)
        data = await ClientCurdHelper().update_client(
            client_id, request.model_dump(exclude_unset=True)
        )
        return data
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))

@client_crud_router.delete('/{client_id}/delete', deprecated=True)
@requires_feature_permission("delete")
async def delete_client(client_id: Annotated[str, Path(title="Client ID", description="Object ID of the client")],
                        current_user: CurrentUser
    ):
    """
    Deletes a specific client. Attention It is a Hard Delete which Delete the Client Permanently.
    For Soft Delete Use Deactivation, This Permission will be only given to the Admin

    ### Path Parameter:
    - **client_id** (str): Object ID of the client.

    ### Response Body:

    - **data** (List[dict]): Contains details about the deleted client.
      - **client_id** (str): Unique identifier of the created client.
      - **document_id** (str): Unique document ID associated with the client.
    - **code** (int): HTTP status code (200 on success).
    - **message** (str): Response message ("Client Created Successfully").
    """
    # TODO AUTHENTICATE & CHECK PERMISSION THROUGH WITH NEW RBAC SYSTEM
    try:
        await UserHelper().is_valid_user(current_user)
        data = await ClientCurdHelper().delete_client(client_id)
        return utility_obj.response_model(data, "Client Deleted Successfully")
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))
