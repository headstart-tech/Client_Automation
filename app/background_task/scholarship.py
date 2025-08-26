"""
This file contains class and functions related to scholarship.
"""
from app.core.background_task_logging import background_task_wrapper
from app.database.configuration import DatabaseConfiguration
from bson import ObjectId
from app.database.aggregation.get_all_applications import Application


class ScholarshipActivity:
    """
    Contain functions related to scholarship.
    """

    async def get_eligible_applicants_info(
            self, programs_info: dict, normal_filters: dict, advance_filters: list, college_id: str,
            get_count_only: bool = False) -> int | list:
        """
        Get information of scholarship eligible applications.

        Params:
            - programs_info (dict): A dictionary which contains program (s) information.
            - normal_filters (dict): A dictionary which contains normal/pre-defined filters information.
            - advance_filters (list): A list of dictionaries which contains advance filters information.
            - college_id (str): An unique identifier/id of college.
            - get_count_only (bool): Default value: False. value will be true when only want eligible applicants count.

        Returns: Return integer value which represent eligible applicants count when parameter
            `get_count_only` value will be true else a list which contains eligible applicants ids.
        """
        payload = {"advance_filters": advance_filters, "course": programs_info}
        if normal_filters:
            payload.update({"annual_income": normal_filters.get("annual_income"),
                            "category": normal_filters.get("category"),
                            "gender": normal_filters.get("gender"), "country_id": normal_filters.get("country_id"),
                            "state": {"state_code": normal_filters.get("state_code")}, "city":
                                {"city_name": normal_filters.get("city_name")}})
        aggregation_pipeline = await Application().all_applications(
            payload=payload,
            college_id=college_id,
            call_segments=True
        )
        if get_count_only:
            aggregation_pipeline.append({"$count": "count"})
            aggregation_result = await DatabaseConfiguration().studentApplicationForms. \
                aggregate(aggregation_pipeline).to_list(None)
            eligible_applicant_counts = aggregation_result[0].get("count") if aggregation_result else 0
            return eligible_applicant_counts
        aggregation_pipeline.append({
            "$group": {
                "_id": None,
                "application_ids": {"$push": "$_id"}
            }
        })
        aggregation_result = await DatabaseConfiguration().studentApplicationForms. \
            aggregate(aggregation_pipeline).to_list(None)
        try:
            eligible_applicants = aggregation_result[0].get("application_ids", [])
        except IndexError:
            eligible_applicants = []
        return eligible_applicants

    @background_task_wrapper
    async def update_eligible_applicants_info_in_db(self, programs_info: dict, normal_filters: dict,
                                                    advance_filters: list,
                                                    college_id: str, scholarship_id: str) -> None:
        """
        Update eligible applications information in the DB.

        Params:
            - programs_info (dict): A dictionary which contains program (s) information.
            - normal_filters (dict): A dictionary which contains normal/pre-defined filters information.
            - advance_filters (list): A list of dictionaries which contains advance filters information.
            - college_id (str): An unique identifier/id of college.
            - scholarship_id (str): An unique identifier/id of scholarship.

        Returns: None
        """
        eligible_applicants = await self.get_eligible_applicants_info(
            programs_info, normal_filters, advance_filters, college_id)
        await DatabaseConfiguration().scholarship_collection.update_one(
            {"_id": ObjectId(scholarship_id)}, {"$set": {"initial_eligible_applicants": eligible_applicants,
                                                         "initial_eligible_applicants_count":
                                                             len(eligible_applicants)}})
