"""
This file contains class and functions related to advance filter.
"""
from app.core.utils import utility_obj
from bson import ObjectId


class AdvanceFilterHelper:
    """
    Contains operations related to advance filter.
    """

    async def perform_operation_based_on_operator(
            self, value: list | None, operator: str | None, query_list: list,
            field_name: str | None, equality_cond: str | None = "$or") -> None:
        """
        Perform operation based on operator and extend query list.

        Params:
            - value (list | None): Either None or a list which contains
                filterable entity value (s).
            - operator (str | None): Either None or a string value which
                represents operation value.
            - query_list (list): A query list which want to extend by
                adding filter.
            - field_name (str | None): Either None or name of a field.
            - equality_cond (str | None): Equality condition which useful
                when want data based on equality. Default value: "$or".

        Returns: None
        """
        if operator in ["Is Null", "Is Blank"]:
            query_list.append(
                {field_name: {"$exists": False}})
        elif operator in ["Is Not Blank"]:
            query_list.append(
                {field_name: {"$exists": True}})
        elif operator in ["Equal", "Is", "Is Equal To"] and value:
            query_list.append({equality_cond: value})
        elif operator in ["Not Equal", "Not Equal To"] and value:
            query_list.append({"$nor": value})

    async def get_collection_info_for_lead_filter(self, field_name: str) \
            -> tuple:
        """
        Get the collection information like collection_field_name, collection_name,
        operator, value and field_name for lead filter.

        Params:
            - field_name (str): Name of a field.

        Returns:
            - tuple: A tuple which contains collection information like
                collection_field_name and collection_name.
        """
        collection_name = "studentsPrimaryDetails"
        collection_field_name = "is_verify"
        if field_name == "state":
            collection_field_name = "address_details.communicati" \
                                    "on_address.state.state_code"
        elif field_name == "source":
            collection_field_name = "source.primary_source." \
                                    "utm_source"
        elif field_name == "lead type":
            collection_field_name = "source.primary_source." \
                                    "lead_type"
        return collection_field_name, collection_name

    async def get_collection_info_for_application_filter(
            self, field_name: str) -> tuple:
        """
        Get the collection information like collection_field_name, collection_name,
        operator, value and field_name for application filter.

        Params:
            - field_name (str): Name of a field.

        Returns:
            - tuple: A tuple which contains collection information like
                collection_field_name and collection_name.
        """
        collection_name = "studentApplicationForms"
        collection_field_name = "declaration"
        if field_name == "counselor":
            collection_field_name = "allocate_to_counselor." \
                                    "counselor_id"
        elif field_name == "application filling stage":
            collection_field_name = "current_stage"
        return collection_field_name, collection_name

    async def get_collection_info_for_secondary_filter(
            self, field_name: str) -> tuple:
        """
        Get the collection information like collection_field_name, collection_name,
        operator, value and field_name for secondary filter.

        Params:
            - field_name (str): Name of a field.

        Returns:
            - tuple: A tuple which contains collection information like
                collection_field_name and collection_name.
        """
        collection_name = "studentSecondaryDetails"
        collection_field_name = "education_details." \
                                "inter_school_details.board"
        if field_name == "12th marks":
            collection_field_name = "education_details.inter" \
                                    "_school_details.obtained_cgpa"
        return collection_field_name, collection_name

    async def get_collection_info_by_normal_filters(
            self, collection_name: str, field_name: str,
            collection_field_name: str | None) -> tuple:
        """
        Get the collection information like collection_field_name, collection_name,
        operator, value and field_name by on normal filter (s) information.

        Params:
            - collection_name (str | None): Either None or a string value which
                represents collection name.
            - field_name (str): Name of a field.
            - collection_field_name (str | None): Either None or a string value
                which useful for filter data.

        Returns:
            - tuple: A tuple which contains collection information like
                collection_field_name and collection_name.
        """
        if collection_name in [None, ""] and \
                field_name in ["state", "source", "lead type",
                               "verify status", "lead stage", "counselor",
                               "application stage",
                               "application filling stage", "12th board",
                               "12th marks"]:
            if field_name in ["state", "source", "lead type",
                              "verify status", "utm medium"]:
                collection_field_name, collection_name = \
                    await self.get_collection_info_for_lead_filter(field_name)
            if field_name in ["counselor", "application stage",
                              "application filling stage"]:
                collection_field_name, collection_name = \
                    await self.get_collection_info_for_application_filter(
                        field_name)
            if field_name == "lead stage":
                collection_name, collection_field_name = "leadsFollowUp", \
                    "lead_stage"
            if field_name in ["12th board", "12th marks"]:
                collection_field_name, collection_name = \
                    await self.get_collection_info_for_secondary_filter(
                        field_name)
        return collection_field_name, collection_name

    async def get_filter_info(self, filter_option: dict) -> tuple:
        """
        Get the filter information like collection_field_name, collection_name,
        operator, value and field_name.

        Params:
            - filter_option (dict): A dictionary which contains block
                information like block condition, filterable condition (s) and
                other information.

        Returns:
            - tuple: A tuple which contains filter information like
                collection_field_name, collection_name, operator, value and
                field_name.
        """
        collection_field_name = filter_option.get(
            "collection_field_name", "")
        collection_name = filter_option.get("collection_name", "")
        operator = filter_option.get("operator")
        value = filter_option.get("value")
        field_name = filter_option.get("fieldName", "").lower()
        collection_field_name, collection_name = \
            await self.get_collection_info_by_normal_filters(
                collection_name, field_name, collection_field_name)
        return collection_field_name, collection_name, operator, value, \
            field_name

    async def update_filter_info(
            self, field_name_selector: dict, collection_name: str,
            collection_field_name: str | None, field_name: str, value: any) \
            -> tuple:
        """
        Update the filter information.

        Params:
            - field_name_selector (dict): A dictionary which useful for change
                collection_field_name which further use for filter data.
            - collection_name (str): Name of a collection which useful for
                filter data.
            - collection_field_name (str | None): Either None or a collection
                field name which use for filter data.
            - field_name (str): Name of a field.
            - value (any): Value which useful for get filterable data.

        Returns:
            - tuple: A tuple which contains updated collection_field_name and
                value.
        """
        if field_name_selector.get(collection_name):
            collection_field_name = f"{field_name_selector.get(collection_name)}." \
                                    f"{collection_field_name}"
        if field_name == "lead type":
            value = value.lower()
        if field_name == "application stage":
            value = True if str(value).lower() == "completed" else False
        if field_name == "email unsubscribe status":
            value = bool(value)
        if field_name in ["verify status", "mobile verification status",
                          "lead verification status",
                          "email verification status"]:
            value = True if str(value).lower() == "verified" else False
        if field_name == "lead owner" and field_name_selector.get(
                "studentsPrimaryDetails"):
            collection_field_name = "allocate_to_counselor.counselor_id"
        if field_name == "form initiated":
            value = True if value == "true" else False
        if field_name in ["payment mode"] and isinstance(value, list):
            value = ["Demand Draft" if payment_mode == "DD" else payment_mode.lower()
                     for payment_mode in value if isinstance(payment_mode, str)]
        if field_name == "application filling stage":
            value = [current_stage.get("current_stage")
                     for current_stage in value]
        if field_name in ["gd status", "pi status"] and \
                isinstance(value, list) and "Slot not booked" in value:
            value.append(None)
        return collection_field_name, value

    async def filter_data_by_utm_medium(
            self, field_name_selector: dict, value: list, operator: str | None,
            query_list: list, field_name: str) -> None:
        """
        Filter data by utm medium.

        Params:
            - field_name_selector (dict): A dictionary which useful for change
                collection_field_name which further use for filter data.
            - value (list): Value which useful for get filterable data.
            - operator (str | None): Either None or a string value which
                represents operation value.
            - query_list (list): A query list which want to extend by
                adding filter.
            - field_name (str | None): Either None or name of a field.

        Returns: None
        """
        collection_field_name = \
            field_name_selector.get("studentsPrimaryDetails")
        if collection_field_name:
            utm_field_name = f"{collection_field_name}.source." \
                             f"primary_source.utm_medium"
            source_field_name = f"{collection_field_name}.source." \
                                f"primary_source.utm_source"
        else:
            utm_field_name = "source.primary_source.utm_medium"
            source_field_name = "source.primary_source.utm_source"
        value = [
            {source_field_name: utm_medium_data.get("source_name"),
             utm_field_name: utm_medium_data.get("utm_medium")}
            for utm_medium_data in value]
        await self.perform_operation_based_on_operator(
            value, operator, query_list, field_name)

    async def extend_source_type_list(
            self, collection_field_name: str | None, source_type: list,
            _type: str) -> None:
        """
        Extend source type list.

        Params:
            - collection_field_name (str | None): Either None or a collection
                field name which use for filter data.
            - source_type (list): A source type list which want to extend by
                adding filter.
            - _type (str): Type of a source.

        Returns: None
        """
        if collection_field_name:
            field_name = f"{collection_field_name}.source." \
                         f"{_type}_source"
        else:
            field_name = f"source.{_type}_source"
        source_type.append({field_name: {"$exists": True}})

    async def filter_data_by_source_type(
            self,  field_name_selector: dict, value: list,
            operator: str | None, query_list: list, field_name: str) -> None:
        """
        Filter data by source type.

        Params:
            - field_name_selector (dict): A dictionary which useful for change
                collection_field_name which further use for filter data.
            - value (list): Value which useful for get filterable data.
            - operator (str | None): Either None or a string value which
                represents operation value.
            - query_list (list): A query list which want to extend by
                adding filter.
            - field_name (str | None): Either None or name of a field.

        Returns: None
        """
        source_type = []
        collection_field_name = \
            field_name_selector.get("studentsPrimaryDetails")
        if "primary" in value:
            await self.extend_source_type_list(
                collection_field_name, source_type, "primary")
        if "secondary" in value:
            await self.extend_source_type_list(
                collection_field_name, source_type, "secondary")
        if "tertiary" in value:
            await self.extend_source_type_list(
                collection_field_name, source_type, "tertiary")
        await self.perform_operation_based_on_operator(
            source_type, operator, query_list, field_name, "$and")

    async def filter_data_by_program(
            self,  field_name_selector: dict, value: list,
            operator: str | None, query_list: list, field_name: str) -> None:
        """
        Filter data by program.

        Params:
            - field_name_selector (dict): A dictionary which useful for change
                collection_field_name which further use for filter data.
            - value (list): Value which useful for get filterable data.
            - operator (str | None): Either None or a string value which
                represents operation value.
            - query_list (list): A query list which want to extend by
                adding filter.
            - field_name (str | None): Either None or name of a field.

        Returns: None
        """
        collection_field_name = \
            field_name_selector.get("studentApplicationForms")
        if collection_field_name:
            course_id = f"{collection_field_name}.course_id"
            spec_name = f"{collection_field_name}.spec_name1"
            app_program_filter = [{"$and": [
                {course_id: {"$in": [ObjectId(program.get(
                    "course_id"))]}},
                {spec_name: {"$in": [program.get(
                    "course_specialization")]}}]}
                for program in value]
        else:
            course_id = "course_id"
            spec_name = "spec_name1"
            app_program_filter = [{"$and": [
                {course_id: ObjectId(program.get("course_id"))},
                {spec_name: program.get("course_specialization")}]}
                for program in value]
        await self.perform_operation_based_on_operator(
            app_program_filter, operator, query_list, field_name)

    async def filter_data_by_form_filling_stage(
            self,  field_name_selector: dict, value: list,
            operator: str | None, query_list: list, field_name: str) -> None:
        """
        Filter data by form filling stage.

        Params:
            - field_name_selector (dict): A dictionary which useful for change
                collection_field_name which further use for filter data.
            - value (list): Value which useful for get filterable data.
            - operator (str | None): Either None or a string value which
                represents operation value.
            - query_list (list): A query list which want to extend by
                adding filter.
            - field_name (str | None): Either None or name of a field.

        Returns: None
        """
        form_filling = []
        if "12th" in value:
            form_filling.append(
                {
                    "student_education_details.education_details"
                    ".inter_school_details.is_pursuing": False})
        if "10th" in value:
            form_filling.append(
                {
                    "student_education_details.education_details"
                    ".tenth_school_details": {
                        "$exists": True}})
        if "Declaration" in value:
            form_filling.append({"declaration": True})
        await self.perform_operation_based_on_operator(
            form_filling, operator, query_list, field_name, "$and")

    async def extend_payment_data_list(
            self, collection_field_name: str | None, payment_data: list,
            value: str) -> None:
        """
        Extend payment data list.

        Params:
            - collection_field_name (str | None): Either None or a collection
                field name which use for filter data.
            - payment_data (list): A payment data list which want to extend by
                adding filter.
            - value (str): value which used for filter data.

        Returns: None
        """
        if collection_field_name:
            payment_data.append({f"{collection_field_name}.payment"
                                 f"_info.status": value})
        else:
            payment_data.append({"payment_info.status": value})

    async def filter_data_by_payment_status(
            self,  field_name_selector: dict, value: list,
            operator: str | None, query_list: list, field_name: str) -> None:
        """
        Filter data by payment status.

        Params:
            - field_name_selector (dict): A dictionary which useful for change
                collection_field_name which further use for filter data.
            - value (list): Value which useful for get filterable data.
            - operator (str | None): Either None or a string value which
                represents operation value.
            - query_list (list): A query list which want to extend by
                adding filter.
            - field_name (str | None): Either None or name of a field.

        Returns: None
        """
        payment_data = []
        collection_field_name = field_name_selector.get(
            "studentApplicationForms")
        if collection_field_name:
            field_name = f"{collection_field_name}.payment_info.status"
        else:
            field_name = "payment_info.status"
        if "Successful" in value or "captured" in value:
            await self.extend_payment_data_list(
                collection_field_name, payment_data, "captured")
        if "Failed" in value or "failed" in value:
            await self.extend_payment_data_list(
                collection_field_name, payment_data, "failed")
        if "refunded" in value or "Refunded" in value:
            await self.extend_payment_data_list(
                collection_field_name, payment_data, "refunded")
        if "In Progress" in value or "started" in value:
            if collection_field_name:
                payment_data.append(
                    {f"{collection_field_name}.payment_initiated":
                         True, f"{collection_field_name}.payment_"
                               f"info.status": {"$ne": "captured"}})
            else:
                payment_data.append({"$and": [
                    {"payment_initiated": True},
                    {"payment_info.status": {"$ne": "captured"}}]})
        if "not started" in value:
            if collection_field_name:
                payment_data.append(
                    {f"{collection_field_name}.payment_initiated":
                         False})
            else:
                payment_data.append({"payment_initiated": False})
        await self.perform_operation_based_on_operator(
            payment_data, operator, query_list, field_name)

    async def filter_by_equality_operator(
            self, value: any, field_name: str, query_list: list,
            collection_field_name: str | None) -> None:
        """
        Filter data by equality operator.

        Params:
            - value (list): Value which useful for get filterable data.
            - field_name (str | None): Either None or name of a field.
            - query_list (list): A query list which want to extend by
                adding filter.
            - collection_field_name (str | None): Either None or a collection
                field name which use for filter data.


        Returns: None
        """
        if isinstance(value, str):
            if field_name in ["counselor", "lead owner", "user id", "auditor name", "previous lead owner",
                              "head counselor", "user name"]:
                value = ObjectId(value)
            query_list.append({collection_field_name: value})
        elif isinstance(value, list):
            if field_name in ["counselor", "lead owner", "user id", "auditor name", "previous lead owner",
                              "head counselor", "user name"]:
                value = [ObjectId(_id) for _id in value if
                         await utility_obj.is_length_valid(
                             _id, field_name.title())]

            for _id, str_value in enumerate(value):
                if isinstance(str_value, str) and "-" in str_value and \
                        field_name == "12th marks":
                    str_value_split = str_value.split("-")
                    value[_id] = {'$and': [{
                        'student_education_details.education_details.inter_school_details.marking_scheme': 'Percentage'},
                        {collection_field_name: {
                            "$gte": float(
                                str_value_split[0]),
                            "$lt": float(
                                str_value_split[
                                    1])}}]}
            if isinstance(value[0], dict):
                query_list.append({"$or": value})
            else:
                query_list.append(
                    {collection_field_name: {"$in": value}})
        else:
            query_list.append({collection_field_name: value})

    async def filter_data_by_date(
            self, value: dict | None, operator: str | None,
            field_type: str, query_list: list,
            collection_field_name: str | None) -> None:
        """
        Filter data by date.

        Params:
            - value (list): Value which useful for get filterable data.
            - operator (str | None): Either None or a string value which
                represents operation value.
            - field_type (str): Type of a field.
            - query_list (list): A query list which want to extend by
                adding filter.
            - collection_field_name (str | None): Either None or a collection
                field name which use for filter data.

        Returns: None
        """
        if value is None:
            value = {}
        if operator in ["Is", "After", "Before"]:
            operator_replacement = {"Is": "$eq", "After": "$gt",
                                    "Before": "$lte"}
            start_date = value.get("start_date")
            if field_type in ["date", "year"]:
                if field_type != "year":
                    start_date, end_date = await utility_obj.date_change_format(
                        start_date, start_date)
                    if operator == "After":
                        start_date = end_date
                else:
                    start_date = int(start_date)
            if operator == "Is" and field_type == "date":
                query_list.append(
                    {collection_field_name:
                         {"$gte": start_date, "$lte": end_date}})
            else:
                query_list.append(
                    {collection_field_name:
                         {operator_replacement.get(operator): start_date}})
        elif operator == "Is Null":
            query_list.append(
                {collection_field_name: {"$exists": False}})
        elif operator == "Between":
            start_date = value.get("start_date")
            end_date = value.get("end_date")
            if field_type != "year":
                start_date, end_date = await utility_obj.date_change_format(
                    start_date, end_date)
            else:
                start_date = int(start_date)
                end_date = int(end_date)
            query_list.append(
                {collection_field_name: {"$gte": start_date,
                                         "$lte": end_date}})

    async def filter_data_by_number(
            self, value: any, operator: str | None, query_list: list,
            collection_field_name: str | None, field_name: str | None) \
            -> None:
        """
        Filter data by number.

        Params:
            - value (any): Value which useful for get filterable data.
            - operator (str | None): Either None or a string value which
                represents operation value.
            - query_list (list): A query list which want to extend by
                adding filter.
            - collection_field_name (str | None): Either None or a collection
                field name which use for filter data.
            - field_name (str | None): Either None or name of a field.

        Returns: None
        """
        if operator == "Between":
            if field_name == "12th marks":
                query_list.append(
                    {'$and': [{
                        'student_education_details'
                        '.education_details'
                        '.inter_school_details.marking_scheme':
                            'Percentage'},
                        {collection_field_name:
                             {"$gte": float(value.get("value1")),
                              "$lt": float(value.get("value2"))}}]})
            else:
                query_list.append(
                        {collection_field_name:
                             {"$gte": float(value.get("value1")),
                              "$lt": float(value.get("value2"))}})
        else:
            operator_replacement = {"Greater Than": "$gt",
                                    "Greater Than Equal To": "$gte",
                                    "Smaller Than": "$lt",
                                    "Smaller Than Equal To": "$lte",
                                    }
            query_list.append(
                {collection_field_name:
                    {operator_replacement.get(operator): float(
                        value)}})

    # TODO - We'll segregate below function into multiple sub-functions
    async def build_query(
            self, filter_block: dict, student_primary: str | None = None,
            courses: str | None = None, student_secondary: str | None = None,
            lead_followup: str | None = None,
            student_application: str | None = None,
            communication_log: str | None = None,
            queries: str | None = None) -> list:
        """
        Build a query which useful for get data based on query.

        Params:
            - filter_block (dict): A dictionary of filterable queries data.
            - student_primary (str | None): Either None or a string which
                useful for get field from student primary collection.
            - courses (str | None): Either None or a string which
                useful for get field from courses collection.
            - student_secondary (str | None): Either None or a string which
                useful for get field from student secondary collection.
            - lead_followup (str | None): Either None or a string which
                useful for get field from lead followup collection.
            - student_application (str | None): Either None or a string which
                useful for get field from student application collection.
            - communication_log (str | None): Either None or a string which
                useful for get field from communication log collection.
            - queries (str | None): Either None or a string which
                useful for get field from queries collection.

        Returns:
            - list: A list which contains filterable query list.
        """
        query_list = []
        for filter_option in filter_block.get("filterOptions", []):
            collection_field_name, collection_name, operator, value, \
                field_name = await self.get_filter_info(filter_option)
            field_name_selector = \
                {"studentsPrimaryDetails": student_primary,
                 "courses": courses,
                 "studentSecondaryDetails": student_secondary,
                 "leadsFollowUp": lead_followup,
                 "studentApplicationForms": student_application,
                 "communicationLog": communication_log, "queries": queries}
            if filter_option.get("fieldType") in ["number"] and isinstance(value, str):
                value = float(value)
            collection_field_name, value = await self.update_filter_info(
                field_name_selector, collection_name, collection_field_name,
                field_name, value)
            if field_name in ["utm medium", "source type",
                              "form filling stage", "payment status"]:
                await getattr(self, f"filter_data_by_{field_name.replace(' ', '_')}")(
                    field_name_selector, value, operator, query_list,
                    field_name)
            elif field_name in ["course", "program"]:
                await self.filter_data_by_program(
                    field_name_selector, value, operator, query_list,
                    field_name)
            elif operator in ["Between", "Before", "After", "Is"] and \
                    filter_option.get("fieldType") in ["date", "year"]:
                await self.filter_data_by_date(
                    value, operator, filter_option.get("fieldType"),
                    query_list, collection_field_name)
            elif operator in ["Greater Than", "Greater Than Equal To",
                              "Smaller Than", "Smaller Than Equal To",
                              "Between"]:
                await self.filter_data_by_number(
                    value, operator, query_list, collection_field_name,
                    field_name)
            elif operator in ["Equal", "Is", "Is Equal To"]:
                await self.filter_by_equality_operator(
                    value, field_name, query_list, collection_field_name)
            elif operator in ["Not Equal", "Not Equal To"]:
                if isinstance(value, str) or isinstance(value, float) or isinstance(value, int):
                    if field_name in ["counselor", "lead owner", "user id", "auditor name", "previous lead owner",
                                      "head counselor", "user name"] and isinstance(value, str):
                        value = ObjectId(value)
                    query_list.append({collection_field_name: {"$ne": value}})
                if isinstance(value, list):
                    if field_name in ["counselor", "lead owner", "user id", "auditor name", "previous lead owner",
                                      "head counselor", "user name"]:
                        value = [ObjectId(_id) for _id in value if
                                 await utility_obj.is_length_valid(
                                     _id, field_name.title)]
                    query_list.append({collection_field_name: {"$nin": value}})
            elif operator in ["Is Null", "Is Blank"]:
                query_list.append({collection_field_name: {"$exists": False}})
            elif operator in ["Is Not Blank"]:
                query_list.append({collection_field_name: {"$exists": True}})
        return query_list

    async def apply_advance_filter(
            self, advance_filters: list[dict], pipeline: list,
            student_primary: str | None = None, courses: str | None = None,
            student_secondary: str | None = None,
            lead_followup: str | None = None,
            student_application: str | None = None, communication_log=None,
            queries=None) -> list:
        """
        Add advance filter query in the aggregation pipeline.

        Params:
            - advance_filters (list[dict]): A list of dictionaries which
                contains fields data along with value (s).
            - pipeline (list): An aggregation pipeline which want to update
                based on advance filter fields along with values.
            - student_primary (str | None): Either None or a string which
                useful for get field from student primary collection.
            - courses (str | None): Either None or a string which
                useful for get field from courses collection.
            - student_secondary (str | None): Either None or a string which
                useful for get field from student secondary collection.
            - lead_followup (str | None): Either None or a string which
                useful for get field from lead followup collection.
            - student_application (str | None): Either None or a string which
                useful for get field from student application collection.
            - communication_log (str | None): Either None or a string which
                useful for get field from communication log collection.
            - queries (str | None): Either None or a string which
                useful for get field from queries collection.

        Returns:
            - list: A list which contains updated aggregation pipeline.
        """
        main_query_list = []

        for block in advance_filters:
            block_condition = block.get("blockCondition", "AND")
            filter_query = await self.build_query(
                block, student_primary=student_primary, courses=courses,
                student_secondary=student_secondary,
                lead_followup=lead_followup,
                student_application=student_application,
                communication_log=communication_log, queries=queries)

            if block_condition == "AND":
                main_query_list.append({"$and": filter_query})
            elif block_condition == "OR":
                main_query_list.append({"$or": filter_query})

            if "conditionBetweenBlock" in block:
                condition_between_block = block.get("conditionBetweenBlock")
                if condition_between_block == "AND":
                    main_query_list = [{"$and": main_query_list}]
                elif condition_between_block == "OR":
                    main_query_list = [{"$or": main_query_list}]

        if main_query_list:
            pipeline.append({"$match": {"$and": main_query_list}})
        return pipeline
