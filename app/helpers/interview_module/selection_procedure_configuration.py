"""
This file contains class and functions related to selection procedure of interview module
"""
import asyncio
import datetime

from bson import ObjectId
from fastapi.exceptions import HTTPException

from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration
from app.helpers.college_configuration import CollegeHelper
from app.helpers.template.template_configuration import TemplateActivity
from app.helpers.user_curd.user_configuration import UserHelper


class SelectionProcedure:
    """
    Contains functions related to selection procedure of interview module
    """

    async def selection_procedure_helper(self,
                                         selection_procedure_data: dict) -> dict:
        """
        Helper function for format selection procedure data

        Params:
            selection_procedure_data (dict): A selection procedure data which need to format.

        Returns:
            dict: A dictionary which contains formatted selection procedure data for avoid error such as ValueError.
        """
        return {"procedure_id": str(selection_procedure_data.get("_id")),
                "course_name": selection_procedure_data.get("course_name"),
                "specialization_name": selection_procedure_data.get(
                    "specialization_name"),
                "eligibility_criteria": selection_procedure_data.get(
                    "eligibility_criteria"),
                "gd_parameters_weightage": selection_procedure_data.get(
                    "gd_parameters_weightage"),
                "pi_parameters_weightage": selection_procedure_data.get(
                    "pi_parameters_weightage"),
                "offer_letter": {key: str(value)
                                 for key, value in
                                 selection_procedure_data.get("offer_letter",
                                                              {}).items()},
                "created_by": str(selection_procedure_data.get("created_by")),
                "created_at": utility_obj.get_local_time(
                    selection_procedure_data.get("created_at")),
                "created_by_name": selection_procedure_data.get(
                    "created_by_name"),
                "last_modified_timeline":
                    [{
                        "last_modified_at":
                            utility_obj.get_local_time(
                                timeline.get("last_modified_at")),
                        "user_id": str(timeline.get("user_id")),
                        "user_name": timeline.get("user_name"),
                    } for timeline in
                        selection_procedure_data.get("last_modified_time",
                                                     [])],
                }

    async def is_valid_user_and_role(self, current_user: str) -> dict:
        """
        Helper function to check if the user is valid and has the correct role.

        Params:
            current_user (str): An user_name of user.

        Returns:
            dict: A dictionary which contains user data.
        """
        user = await UserHelper().is_valid_user(current_user)
        if user.get("role", {}).get("role_name") not in ["college_super_admin",
                                                         "college_admin"]:
            raise HTTPException(status_code=401,
                                detail=f"Not enough permissions")
        return user

    async def is_valid_selection_procedure(self, procedure_id):
        """
        Helper function to fetch the selection procedure from the database based on id.

        Params:
            procedure_id (str): An unique id for get selection procedure data.

        Returns:
            dict: A dictionary which contains selection procedure data.
        """
        await utility_obj.is_id_length_valid(_id=procedure_id,
                                             name="Procedure id")
        selection_procedure = await DatabaseConfiguration().selection_procedure_collection.find_one(
            {"_id": ObjectId(procedure_id)})
        if not selection_procedure:
            raise HTTPException(
                status_code=404,
                detail="Selection procedure not found. Make sure provided procedure id should be correct.")
        return selection_procedure

    async def update_selection_procedure_data(self, procedure_id: str,
                                              selection_procedure_data: dict,
                                              last_modified_timeline: list) -> dict:
        """
        Update selection procedure data

        Params:
            procedure_id (str): An unique id for update selection procedure of course.
            selection_procedure_data (dict): A data which useful for update selection procedure of course.
            user (dict): A dictionary which contains user data.
            current_datetime (datetime): current date and time in utc format.
            last_modified_timeline (list): A list which contains last modified timeline data such user_id,
                                           user_name and datetime.

        Returns:
            dict: A dictionary which contains update selection procedure data info.
        """
        selection_procedure = await self.is_valid_selection_procedure(
            procedure_id)
        course_name = selection_procedure_data.get('course_name')
        if course_name and course_name != selection_procedure.get(
                'course_name'):
            if await DatabaseConfiguration().selection_procedure_collection.find_one(
                    {'course_name': selection_procedure_data.get(
                        'course_name'),
                        "specialization_name": selection_procedure_data.get(
                            'specialization_name')}) is not None:
                return {'detail': 'Selection procedure already exists.'}
        selection_procedure.get("last_modified_timeline", []).insert(0,
                                                                     last_modified_timeline[
                                                                         0])
        selection_procedure_data.update({
            "last_modified_timeline": selection_procedure.get(
                "last_modified_timeline")})
        await DatabaseConfiguration().selection_procedure_collection.update_one(
            {"_id": ObjectId(procedure_id)}, {"$set": selection_procedure_data}
        )
        return {"message": "Selection procedure data updated."}

    async def delete_selection_procedure(self, current_user: str,
                                         procedure_id: str) -> dict:
        """
        Delete selection procedure.

        Params:
            current_user (str): An user_name of user.
            procedure_id (str): An unique id for delete selection procedure.

        Returns:
            dict: A dictionary which contains delete selection procedure info.
        """
        await self.is_valid_user_and_role(current_user)
        await self.is_valid_selection_procedure(procedure_id)
        await DatabaseConfiguration().template_collection.delete_one(
            {"_id": ObjectId(procedure_id)})
        return {"message": "Selection procedure deleted."}

    async def get_selection_procedure(self, current_user: str,
                                      procedure_id: str) -> dict:
        """
        Get selection procedure info.

        Params:
            current_user (str): An user_name of user.
            procedure_id (str): An unique id for delete selection procedure.

        Returns:
            dict: A dictionary which contains get selection procedure info.
        """
        await self.is_valid_user_and_role(current_user)
        selection_procedure = await self.is_valid_selection_procedure(
            procedure_id)
        return {"message": "Get Selection procedure data.",
                "data": await self.selection_procedure_helper(
                    selection_procedure)}

    async def add_selection_procedure_data(self,
                                           selection_procedure_data: dict,
                                           current_datetime: datetime,
                                           last_modified_timeline: list,
                                           user: dict) -> dict:
        """
        Add selection procedure data.

        Params:
            selection_procedure_data (dict): A data which useful for create selection procedure of course.
            current_datetime (datetime): current date and time in utc format.
            last_modified_timeline (list): A list which contains last modified timeline data such user_id,
            user_name and datetime.
            user (dict): A dictionary which contains user data.

        Returns:
            dict: A dictionary which contains add selection procedure data info.
        """
        if selection_procedure_data.get("course_name", "") in ["", None]:
            raise HTTPException(status_code=422,
                                detail="Course name must be required and valid.")
        elif selection_procedure_data.get("offer_letter") is None:
            raise HTTPException(status_code=422,
                                detail="Offer letter details must be required and valid.")
        if await DatabaseConfiguration().selection_procedure_collection.find_one(
                {"course_name": selection_procedure_data.get("course_name"),
                 "specialization_name": selection_procedure_data.get(
                     "specialization_name")}):
            raise HTTPException(status_code=422,
                                detail="Selection procedure for course already exist.")
        selection_procedure_data.update({"created_by": user.get("_id"),
                                         "created_by_name": utility_obj.name_can(
                                             user),
                                         "created_at": current_datetime,
                                         "last_modified_timeline": last_modified_timeline
                                         })
        await DatabaseConfiguration().selection_procedure_collection.insert_one(
            selection_procedure_data)
        return {"message": "Selection procedure data added."}

    async def create_or_update_selection_procedure(self, current_user: str,
                                                   section_procedure_data: dict,
                                                   procedure_id: str) -> dict:
        """
        Create or update selection procedure for course.
        Selection procedure will be based on specialization when there is specialization (s) available for course.

        Params:
            section_procedure_data (dict): A data which useful for create/update selection procedure of course.
            current_user (str): An user_name of current user.
            procedure_id (str): An unique id for update selection procedure of course.

        Returns:
            dict: A dictionary which contains create/update selection procedure data.
        """
        user = await self.is_valid_user_and_role(current_user)
        section_procedure_data = await CollegeHelper().remove_empty_dicts(
            section_procedure_data)
        current_datetime = datetime.datetime.utcnow()
        last_modified_timeline = await TemplateActivity().get_last_timeline(
            user)
        approver_id = section_procedure_data.get("offer_letter", {}).get(
            "authorized_approver")
        if approver_id:
            approver = await DatabaseConfiguration().user_collection.find_one(
                {"_id": ObjectId(approver_id)})
            section_procedure_data["offer_letter"][
                "authorized_approver"] = ObjectId(approver_id)
            section_procedure_data["offer_letter"][
                "authorized_approver_name"] = utility_obj.name_can(approver)
        if procedure_id:
            return await self.update_selection_procedure_data(procedure_id,
                                                              section_procedure_data,
                                                              last_modified_timeline)
        else:
            return await self.add_selection_procedure_data(
                section_procedure_data, current_datetime,
                last_modified_timeline, user)

    async def get_selection_procedures(self, current_user: str, page_num: int,
                                       page_size: int) -> dict:
        """
        Get selection procedure info.

        Params:
            current_user (str): An user_name of user.
            page_num(int): Enter page number where you want to show selection procedures data.
            page_size (int): Enter page size means how many data you want to show on page_num.

        Returns:
            dict: A dictionary which contains selection procedures data.
        """
        await self.is_valid_user_and_role(current_user)
        skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                              page_size)
        pipeline = [
            {
                "$facet": {
                    "paginated_results": [{"$sort": {"created_at": -1}},
                                          {"$skip": skip}, {"$limit": limit}],
                    "totalCount": [{"$count": "count"}],
                }
            }
        ]
        result = DatabaseConfiguration().selection_procedure_collection.aggregate(
            pipeline)
        total_data, data = 0, []
        async for documents in result:
            try:
                total_data = documents.get("totalCount")[0].get("count")
            except IndexError:
                total_data = 0
            gather_data = [self.selection_procedure_helper(document) for
                           document in
                           documents.get("paginated_results", [])]
            data = await asyncio.gather(*gather_data)
        response = await utility_obj.pagination_in_aggregation(page_num,
                                                               page_size,
                                                               total_data,
                                                               "/interview/selection_procedures")
        return {"message": "Get Selection procedure data.",
                "data": data, "total": total_data, "count": page_size,
                "pagination": response.get("pagination")}

    async def delete_selection_procedures_by_ids(
            self, selection_procedure_ids: list[str]) -> dict:
        """
        Delete selection procedures by ids.

        Params:
            selection_procedure_ids (list[str]): A list which contains unique
                identifiers/ids of selection procedure.

        Returns:
              dict: A dictionary contains info about delete selection
              procedures.
        """
        procedure_ids = [ObjectId(procedure_id) for procedure_id in
                    selection_procedure_ids if await utility_obj.
            is_length_valid(procedure_id, "Selection procedure id")]
        await DatabaseConfiguration().selection_procedure_collection.delete_many(
            {"_id": {"$in": procedure_ids}})
        return {"message": "Deleted selection procedures by ids."}


selection_procedure_obj = SelectionProcedure()
