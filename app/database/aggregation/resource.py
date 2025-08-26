"""
This file contain class and functions related to get resource data using
aggregation.
"""
from app.core.log_config import get_logger
from app.database.configuration import DatabaseConfiguration
from app.helpers.resource.updates_config import Updates
from app.core.utils import utility_obj
from app.helpers.resource.category_config import KeyCategory
from bson import ObjectId

logger = get_logger(name=__name__)


class Resource:
    """
    Contain functions related to get resource data.
    """

    async def get_user_updates(
            self, page_num: int | None, page_size: int | None,
            role_name: str, update_id: str | None = None) -> tuple:
        """
        Get the user updates.

        Params:
            - page_num (int | None): Either None or page number where you want
                to data. e.g., 1
            - page_size (int | none): Either None or page size, useful for show
                data on page_num. e.g., 25.
                If we give page_num=1 and page_size=25 i.e., we want 25
                    records on page 1.
            - role_name: Role name of a user.

        Returns:
            tuple: A tuple which contains user updates along with total count.
        """
        roles = ["super_admin", "client_manager", "college_super_admin",
                 "college_admin", "college_head_counselor",
                 "college_counselor", "college_publisher_console", "panelist",
                 "authorized_approver", "moderator"]
        if role_name not in ["super_admin", "client_manager",
                             "college_super_admin", "college_admin",
                             "college_head_counselor"]:
            roles = [role_name]
        elif role_name == "college_head_counselor":
            roles = ["college_head_counselor", "college_counselor"]
        elif role_name in ["college_super_admin", "college_admin"]:
            roles.remove("client_manager")
            roles.remove("super_admin")
        base_match = {"selected_profiles": {"$in": roles}}
        if update_id:
            await utility_obj.is_length_valid(update_id, "Update id")
            base_match = {"_id": ObjectId(update_id)}
        aggregation_pipeline = [
            {"$match": base_match},
            {"$sort": {"created_at": -1}}
        ]
        paginated_results = []
        if page_num and page_size:
            skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                                  page_size)
            paginated_results.extend(
                [{"$skip": skip}, {"$limit": limit}])
        if not update_id:
            paginated_results.append({"$project":
                                          {"_id": {"$toString": "$_id"},
                                           "title": {
                                                   "$cond": {
                                                       "if": {"$gte": [{
                                                           "$strLenCP":
                                                               "$title"},
                                                           686]},
                                                       "then": {
                                                           "$concat": [
                                                               {"$substr": [
                                                                   "$title", 0,
                                                                   686]},
                                                               "..."]},
                                                       "else": "$title"
                                                   }
                                               }, "selected_profiles": 1,
                                           "created_at": 1,
                                           "last_updated_on": 1,
                                           "created_by": {
                                               "$toString": "$created_by"},
                                           "created_by_name": 1, "content":
                                               {
                                                   "$cond": {
                                                       "if": {"$gte": [{
                                                           "$strLenCP":
                                                               "$content"},
                                                           686]},
                                                       "then": {
                                                           "$concat": [
                                                               {"$substr": [
                                                                   "$content",
                                                                   0, 686]},
                                                               "..."]},
                                                       "else": "$content"
                                                   }
                                               }}})
        aggregation_pipeline.append(
            {
                "$facet": {
                    "paginated_results": paginated_results,
                    "totalCount": [{"$count": "count"}],
                }
            }
        )
        result = DatabaseConfiguration().user_updates_collection.aggregate(
            aggregation_pipeline)
        user_updates, total_updates = [], 0
        async for documents in result:
            try:
                total_updates = documents.get("totalCount")[0].get("count")
            except IndexError:
                total_updates = 0
            user_updates = [await Updates().user_update_helper(document)
                            for document in documents.get("paginated_results",
                                                          [])]
        return user_updates, total_updates

    async def get_questions(
            self, page_num: int | None, page_size: int | None,
            question_filter: None | dict, total_only: bool = False
    ) -> tuple | int:
        """
        Get the user updates.

        Params:
            - page_num (int | None): Either None or page number where you want
                to data. e.g., 1
            - page_size (int | none): Either None or page size, useful for show
                data on page_num. e.g., 25.
                If we give page_num=1 and page_size=25 i.e., we want 25
                    records on page 1.
            - question_filter (None | dict): Either None or a dictionary which
                contains filterable fields which useful for get questions
                based on filter.
                e.g., {"search_pattern": "tes",
                    "tags": ["Eligibility", "Course"]}
            - total_only (bool): Default value: False. Useful for get only
                total count of questions.

        Returns:
            tuple | int: A tuple which contains questions along with total
            count or count of questions in case of total_only=True.
        """
        aggregation_pipeline, paginated_results = [], []
        match_filter = []
        search_input = question_filter.get("search_pattern")
        tags = question_filter.get("tags")
        if search_input not in ["", None]:
            name_pattern = f".*{search_input}.*"
            new_pattern = {"$regex": name_pattern, "$options": "i"}
            match_filter.append({"question": new_pattern})
        if tags:
            match_filter.append({"tags": {"$in": tags}})
        program_list = question_filter.get("program_list")
        if program_list:
            program_filter = [
                {"course_name": program.get("course_name"),
                 "course_specialization": program.get("course_specialization"),
                 "course_id": ObjectId(program.get("course_id"))}
                for program in program_list]
            if program_filter:
                match_filter.append({"program_list": {"$in": program_filter}})
        if match_filter:
            aggregation_pipeline.append({"$match": {"$and": match_filter}})
        aggregation_pipeline.append({"$sort": {"created_at": -1}})
        if page_num and page_size:
            skip, limit = await utility_obj.return_skip_and_limit(page_num,
                                                                  page_size)
            paginated_results.extend(
                [{"$skip": skip}, {"$limit": limit}])
        aggregation_pipeline.append(
            {
                "$facet": {
                    "paginated_results": paginated_results,
                    "totalCount": [{"$count": "count"}],
                }
            }
        )
        result = DatabaseConfiguration().questions.aggregate(
            aggregation_pipeline)
        questions, total_questions = [], 0
        async for documents in result:
            try:
                total_questions = documents.get("totalCount")[0].get("count")
            except IndexError:
                total_questions = 0
            if not total_only:
                questions = [await KeyCategory().get_question_helper(document)
                             for document in documents.get("paginated_results",
                                                           [])]
        if total_only:
            return total_questions
        return questions, total_questions
