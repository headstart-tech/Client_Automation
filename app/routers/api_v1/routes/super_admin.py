"""
This file contains API route related to update user permission
"""
from fastapi import APIRouter, Body, Query
from app.core.utils import utility_obj
from app.helpers.admin_dashboard.admin_dashboard import AdminDashboardHelper
from app.models.user_schema import UserPermissionSchema, UserMenuPermission
from app.core.custom_error import DataNotFoundError, CustomError
from fastapi.exceptions import HTTPException

super_router = APIRouter()


@super_router.put("/menu_permission/")
async def menu_permissions(
        user_type: str = Query(
            description="Type of user which user you want to add permission 🚀"
                        " \n* **super_admin** \n* **client_manager** "
                        "\n* **college_super_admin** \n* **college_admin**"
                        " \n* **college_head_counselor** \n* "
                        "**college_counselor** \n* "
                        "**college_publisher_console**"
                        " \n* **panelist** \n* **authorized_approver** "
                        "\n* **moderator**"

        ),
        user_permission: UserPermissionSchema = Body(
            ..., description="give permission true and false"
        ),
):
    """
    Update the menu_permission field in user_collection

    Request Body Params:\n
        - user_type (str): A string value which represents role/user_type name.
            Possible values are super_admin, client_manager, college_super_admin, college_admin,
            college_head_counselor, college_counselor, college_publisher_console, panelist, authorized_approver and
            moderator.
        - user_permission (dict): A dictionary which contains information about users menu and permissions data.

    Returns:\n
         - dict: A dictionary which contains information about update menu and permission.

    Raises:
         - CustomError: An error occurred when user_type/role not found.
         - DataNotFoundError: An error occurred when user_type/role not found.
         - Exception: An error occurred when update menu permission for roles.
    """
    try:
        data = {k: v for k, v in user_permission.model_dump().items() if v is not None}
        check = await AdminDashboardHelper().create_menu_permission(user_type, data)
        return utility_obj.response_model(data=check, message="data update successfully")
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occurred when update menu permission for role "
                                                    f"`{user_type}`. Error - {error}")


@super_router.put("/update_users_menu_permission/")
async def update_menu_permissions_of_users(
        users_menu_permission: list[UserMenuPermission] | list = Body(
            description="A list of users manu and permission"
        )
):
    """
    Update the users menu_permissions for multiple user types.

    Request Body Params:\n
        - users_permission (list[UserPermissionSchema] | list): A list which contains information about
            users menu and permissions data.

    Returns:\n
         - dict: A dictionary which contains information about update menu and permission.

    Raises:
         - CustomError: An error occurred when user_type/role not found.
         - DataNotFoundError: An error occurred when user_type/role not found.
         - Exception: An error occurred when update menu permission for roles.
    """
    try:
        for user_menu_permission_info in users_menu_permission:
            data = {k: v for k, v in dict(user_menu_permission_info).items() if v is not None}
            user_type = data.get("user_type")
            if user_type == "student":
                data.pop("menus", None)
                data.pop("permission", None)
            else:
                data.pop("student_menus", None)
            await AdminDashboardHelper().create_menu_permission(
                user_type, data.get("menus"), data.get("permission"), data.get("student_menus"))
        return {"message": "Updated menu permission."}
    except CustomError as error:
        raise HTTPException(status_code=400, detail=error.message)
    except DataNotFoundError as error:
        raise HTTPException(status_code=404, detail=error.message)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"An error occurred when update users menu permission. "
                                                    f"Error - {error}")
