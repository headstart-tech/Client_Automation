"""
This file contains common useful functions for the various components
"""
from app.database.configuration import DatabaseConfiguration


class Check_payload:

    def __init__(self, collection_index):
        self.collection_index = collection_index
        self.index_field = 0
        self.bool_fields = [
            "state_b",
            "city_b",
            "counselor_b",
            "application_stage_b",
            "lead_b",
            "lead_sub_b",
            "source_b",
            "source_type_b",
            "utm_medium_b",
            "utm_campaign_b",
            "lead_type_b",
            "is_verify_b",
            "date",
            "form_filling_stage_b",
            "twelve_board_b",
        ]

    def check_index(self, collection_name):
        if self.collection_index.get(collection_name, {}):
            if (
                self.index_field
                < list(self.collection_index.get(collection_name, {}).keys())[0]
            ):
                self.index_field = list(
                    self.collection_index.get(collection_name, {}).keys()
                )[0]

    def get_dict_data(self, payload_temp, name=None):
        for key, value in payload_temp.items():
            if key in self.bool_fields:
                continue
            if value:
                if type(value) in [int, str, float, bool]:
                    self.check_index(name)
                if type(value) == list:
                    self.get_list_data(value, name)
                if type(value) == dict:
                    self.get_dict_data(value, name)

    def get_list_data(self, payload_temp, name=None):
        for data_temp in payload_temp:
            if data_temp in self.bool_fields:
                continue
            if data_temp:
                if type(data_temp) in [int, str, float, bool]:
                    self.check_index(name)
                if type(data_temp) == list:
                    self.get_list_data(data_temp, name)
                if type(data_temp) == dict:
                    self.get_dict_data(data_temp, name)

    def get_meal(self, payload, applications=False):
        primary = [
            "is_verify",
            "city",
            "state",
            "state_code",
            "country",
            "source",
            "utm_medium",
            "source_name",
            "lead_type",
            "source_type",
            "city_name",
            "lead_type_name",
        ]
        application = [
            "application_filling_stage",
            "payment_status",
            "course",
            "application_stage",
            "application_stage_name",
        ]
        lead = ["lead_stage", "lead_stage_change", "lead_name"]
        secondary = [
            "twelve_board",
            "form_filling_stage",
            "twelve_marks",
        ]
        if applications:
            application.extend(["counselor_id", "counselor"])
        else:
            primary.extend(["counselor_id", "counselor"])
        for key, value in payload.items():
            if key in self.bool_fields:
                continue
            if key in primary:
                if value:
                    if type(value) in [int, str, float, bool]:
                        self.check_index("studentsPrimaryDetails")
                    if type(value) == dict:
                        self.get_dict_data(value, name="studentsPrimaryDetails")
                    if type(value) == list:
                        self.get_list_data(value, name="studentsPrimaryDetails")
            elif key in application:
                if value:
                    if type(value) in [int, str, float, bool]:
                        self.check_index("studentApplicationForms")
                    if type(value) == dict:
                        self.get_dict_data(value, name="studentApplicationForms")
                    if type(value) == list:
                        self.get_list_data(value, name="studentApplicationForms")
            elif key in lead:
                if value:
                    if type(value) in [int, str, float, bool]:
                        self.check_index("leadsFollowUp")
                    if type(value) == dict:
                        self.get_dict_data(value, name="leadsFollowUp")
                    if type(value) == list:
                        self.get_list_data(value, name="leadsFollowUp")
            elif key in secondary:
                if value:
                    if type(value) in [int, str, float, bool]:
                        self.check_index("studentSecondaryDetails")
                    if type(value) == dict:
                        self.get_dict_data(value, name="studentSecondaryDetails")
                    if type(value) == list:
                        self.get_list_data(value, name="studentSecondaryDetails")
        return self.index_field


class Utils_helper:

    async def Check_address(self,
                            country_code: str | None = None,
                            state_code: str | None = None,
                            city_name: str | None = None):
        """
        Check the country code, state code and city name.

        Param:
            country_code (str): Get the country code of the country.
            state_code (str): Get the state code of the state.
            city_name (str): Get the city name of the

        Returns:
            A dictionary which has details of country name. state name and city name, False
        """
        query, address_details = {}, None
        if country_code:
            query.update({"country_code": country_code.upper()})
        if state_code:
            query.update({"state_code": state_code.upper()})
        if city_name:
            query.update({"name": city_name.title()})
        if query:
            address_details = await DatabaseConfiguration().city_collection.find_one(query)
        return address_details
