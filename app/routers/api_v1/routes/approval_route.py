"""This File contains the API routes for Approval Module"""

from typing import Annotated, Literal, Optional

# Todo: Recheck Again when all Users are created even Higher Hierarchies
#  & All Other Components are Ready which needs approval
from fastapi import APIRouter, HTTPException, Query

from app.core.custom_error import CustomError, DataNotFoundError, NotEnoughPermission
from app.core.utils import requires_feature_permission
from app.dependencies.oauth import CurrentUser
from app.helpers.approval.approval_helper import ApprovalCRUDHelper
from app.helpers.user_curd.user_configuration import UserHelper
from app.models.approval_schema import (
    NewApprovalRequestModel,
    RemarksModel,
    UpdateApprovalRequestModel,
    ApprovalFilterModel,
)

approval_router = APIRouter()


@approval_router.post("/create_request")
@requires_feature_permission("write")
async def create_request(
    current_user: CurrentUser, request_data: NewApprovalRequestModel
):
    """
    Create the approval request

    ### Request Body
    - **approval_type**: str, ["college_onboarding", "student_dashboard", "admin_screen", "student_registration_form"]
    - **approval_data**: dict

    ### Example Body
    ```json
    {
       "approval_type":"college_onboarding",
       "approval_data":{
          "name":"test",
          "logo":"test",
          "background_image":"test",
          "address":{
             "address_line_1":"string",
             "address_line_2":"string",
             "country_code":"string",
             "state_code":"string",
             "city":"string"
          }
       }
    }
    ```
    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **422**: Custom Error (Error will be mentioned in `detail`)
    - **401**: Unauthorized/Not Enough Permissions
    - **400**: Bad Request

    ### Response Body
    - **approval_id**: Approval Id
    - **message**: Approval Request Created Successfully.
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        value = await ApprovalCRUDHelper().create_approval_request(
            user, request_data.model_dump()
        )
        return value
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@approval_router.get("/get_requests")
@requires_feature_permission("read")
async def get_requests(current_user: CurrentUser):
    """
    Get Approval Sent by Client or College

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **422**: Custom Error (Error will be mentioned in `detail`)
    - **401**: Unauthorized/Not Enough Permissions
    - **400**: Bad Request

    ### Response Body
    - **list**: List of all Sent Approvals
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        value = await ApprovalCRUDHelper().get_approval_requests(user)
        return value
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@approval_router.get("/get_request_need_approval")
@requires_feature_permission("read")
async def get_request_need_approval(current_user: CurrentUser):
    """
    Get Approval Received from Client or College

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **422**: Custom Error (Error will be mentioned in `detail`)
    - **401**: Unauthorized/Not Enough Permissions
    - **400**: Bad Request

    ### Response Body
    - **list**: List of all Received Approvals
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        value = await ApprovalCRUDHelper().get_request_need_approval(user)
        return value
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@approval_router.post("/get_all_approval_requests")
@requires_feature_permission("read")
async def get_all_approval_requests(
    current_user: CurrentUser,
    filters: ApprovalFilterModel,
    page: Optional[int] = Query(None, gt=0),
    limit: Optional[int] = Query(None, gt=0),
):
    """
    Get All Approval Requests by Merging get_approval_requests and get_request_need_approval

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **422**: Custom Error (Error will be mentioned in `detail`)
    - **401**: Unauthorized/Not Enough Permissions
    - **400**: Bad Request

    ### Response Body
    - **list**: List of all Received Approvals
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        return await ApprovalCRUDHelper().get_all_approval_requests(
            user,
            filters.model_dump(),
            page,
            limit,
            "/approval/get_all_approval_requests",
        )
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@approval_router.get("/get_request_data/{approver_id}")
@requires_feature_permission("read")
async def get_request_data(current_user: CurrentUser, approver_id: str):
    """
    Get Approval Request Data

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **422**: Custom Error (Error will be mentioned in `detail`)
    - **401**: Unauthorized/Not Enough Permissions
    - **400**: Bad Request

    ### Response Body
    - **list/dict**: Approval requested Data
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        value = await ApprovalCRUDHelper().get_approval_requested_data(
            user, approver_id
        )
        return value
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except NotEnoughPermission as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@approval_router.put("/update_status/{approver_id}")
@requires_feature_permission("edit")
async def update_status(
    current_user: CurrentUser,
    approver_id: str,
    status: Annotated[Literal["approve", "reject"], Query(alias="status")],
    remarks: RemarksModel,
):
    """
    Update Approval Request Status

    ### Params
    - **approver_id**: ObjectId
    - **status**: Literal["approve", "reject"]
    - **remarks**: str

    ### Request Body
    - **remarks**: str

    ### Example Body
    ```json
    {
        "remarks": "Accepted"
    }
    ```

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **422**: Custom Error (Error will be mentioned in `detail`)
    - **401**: Unauthorized/Not Enough Permissions
    - **400**: Bad Request

    ### Response Body
    - **message**: Approval Request Updated Successfully.
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        value = await ApprovalCRUDHelper().approve_reject_approval(
            user, approver_id, status, remarks.model_dump()
        )
        return value
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except NotEnoughPermission as e:
        raise HTTPException(status_code=401, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@approval_router.delete("/delete_request/{approver_id}")
@requires_feature_permission("delete")
async def delete_request(current_user: CurrentUser, approver_id: str):
    """
    Delete the Approval Request

    ### Params
    - **approver_id**: ObjectId

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **422**: Custom Error (Error will be mentioned in `detail`)
    - **401**: Unauthorized/Not Enough Permissions
    - **400**: Bad Request

    ### Response Body
    - **message**: Approval Request Deleted Successfully.
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        value = await ApprovalCRUDHelper().delete_request_sent(user, approver_id)
        return value
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@approval_router.put("/update_request/{approver_id}")
@requires_feature_permission("edit")
async def update_request(
    current_user: CurrentUser,
    approver_id: str,
    request_data: UpdateApprovalRequestModel,
):
    """
    Update the Approval Request

    ### Params
    - **approver_id**: ObjectId
    - **request_data**: dict/list

    ### Raises
    - **404**: Data Not Found
    - **500**: Something went wrong Internally
    - **422**: Custom Error (Error will be mentioned in `detail`)
    - **401**: Unauthorized/Not Enough Permissions
    - **400**: Bad Request

    ### Response Body
    - **message**: Approval Request Updated Successfully.
    """
    # Todo: Implement new RBAC when Ready
    # Todo: Check again When all Users are created even Higher Hierarchies
    user = await UserHelper().is_valid_user(current_user)
    try:
        value = await ApprovalCRUDHelper().update_request(
            user, approver_id, request_data.model_dump().get("approval_data")
        )
        return value
    except CustomError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DataNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="An Error Occurred: " + str(e))


@approval_router.get("/get_metadata")
async def get_metadata():
    """
    Retrieve Approval Metadata which contains Approval Types and Approval Status which are defined in the System

    ### Response Body
    - **approval_metadata**: dict
    """
    return await ApprovalCRUDHelper().get_approval_metadata()
