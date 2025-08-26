"""
This file contain class and functions related to campaign
"""
import datetime

import pandas as pd

from app.core.utils import utility_obj


class CampaignHelper:
    """
    Contain functions related to campaign
    """

    async def campaign_helper(self, data):
        """
        Get campaign details
        """
        return {
            'campaign_id': str(data.get('_id')),
            'campaign_type': data.get('campaign_type'),
            'campaign_name': data.get('campaign_name'),
            'campaign_description': data.get('campaign_description'),
            'filters': data.get('filters'),
            'enabled': data.get('enabled'),
            'is_published': data.get('is_published'),
            'created_by_id': str(data.get('created_by_id')),
            'created_by_name': data.get('created_by_name'),
            'created_on': utility_obj.get_local_time(data.get('created_on')),
            'updated_by': str(data.get('updated_by_id')),
            'updated_by_name': data.get('updated_by_name'),
            'updated_on': utility_obj.get_local_time(data.get('updated_on')),
        }

    async def campaign_rule_helper(self, data):
        """
        Get campaign rule details
        """
        return {
            'campaign_rule_id': str(data.get('_id')),
            'campaign_rule_name': data.get('rule_name'),
            'campaign_rule_description': data.get('campaign_description'),
            'campaign_name': data.get('campaign_name'),
            'script': {'action_type': data.get('script', {}).get('action_type'),
                       'condition_exec': data.get('script', {}).get('condition_exec'),
                       'when_exec': data.get('script', {}).get('when_exec'),
                       'instant_action': data.get('script', {}).get('instant_action'),
                       'selected_template': str(data.get('script', {}).get('selected_template')),
                       'email_subject': data.get('script', {}).get('email_subject')},
            'enabled': data.get('enabled'),
            'is_published': data.get('is_published'),
            'created_by_id': str(data.get('created_by_id')),
            'created_by_name': data.get('created_by_name'),
            'created_on': utility_obj.get_local_time(data.get('created_on')),
            'updated_by': str(data.get('updated_by_id')),
            'updated_by_name': data.get('updated_by_name'),
            'updated_on': utility_obj.get_local_time(data.get('updated_on')),
        }


class RuleHelper:
    """Perform task related to campaign rule."""

    def __init__(self):
        pass

    def get_next_trigger_datetime(self, schedule_type, last_executed_on, schedule_value=1):
        """
        Get next trigger datetime of campaign rule
        """
        if schedule_type.title() == "Day":
            next_trigger_time = utility_obj.get_local_time(
                last_executed_on + datetime.timedelta(days=int(schedule_value)))
        elif schedule_type.title() == "Week":
            next_trigger_time = utility_obj.get_local_time(
                last_executed_on + datetime.timedelta(weeks=int(schedule_value)))
        elif schedule_type.title() == "Month":
            next_trigger_time = utility_obj.get_local_time(
                last_executed_on + pd.offsets.DateOffset(months=int(schedule_value)))
        elif schedule_type.title() == "Hour":
            next_trigger_time = utility_obj.get_local_time(
                last_executed_on + datetime.timedelta(hours=int(schedule_value)))
        elif schedule_type.title() == "Once":
            next_trigger_time = utility_obj.get_local_time(last_executed_on)
        else:
            next_trigger_time = "When condition execute"
        return next_trigger_time

    async def rule_helper(self, data):
        """
        Get rule details
        """
        return {
            'rule_id': str(data.get('_id')),
            'rule_name': data.get('rule_name'),
            'rule_description': data.get('rule_description'),
            'script': {'action_type': data.get('script', {}).get('action_type'),
                       'condition_exec': data.get('script', {}).get('condition_exec'),
                       'when_exec': data.get('script', {}).get('when_exec'),
                       'instant_action': data.get('script', {}).get('instant_action'),
                       'selected_template_ids': [str(item) for item in
                                                 data.get('script', {}).get('selected_template_id')],
                       'email_template_content': data.get('script', {}).get('email_template_content'),
                       'email_subject': str(data.get('script', {}).get('email_subject')),
                       'sms_template_content': data.get('script', {}).get('sms_template_content'),
                       'dlt_content_id': str(data.get('script', {}).get('dlt_content_id'))},
            'whatapp_template_content': data.get('script', {}).get('whatsapp_template_content'),
            'data_segment_name': data.get('data_segment_name'),
            'data_segment_id': str(data.get('data_segment_id')),
            "execution_count": data.get("execution_count") if data.get("execution_count") else 0,
            "failed_execution_count": data.get("failed_execution_count") if data.get("failed_execution_count") else 0,
            "next_trigger_time": self.get_next_trigger_datetime(
                data.get('script', {}).get('when_exec', {}).get('schedule_type'),
                data.get("script", {}).get("when_exec", {}).get("last_execution") if data.get("script", {}).get(
                    "when_exec",
                    {}).get(
                    "last_execution") is not None else data.get("created_on"),
                data.get('script', {}).get('when_exec', {}).get('schedule_value')),
            'enabled': data.get('enabled'),
            'is_published': data.get('is_published'),
            'created_on': utility_obj.get_local_time(data.get('created_on')),
            'created_by_id': str(data.get('created_by_id')),
            'created_by_name': data.get('created_by_name'),
            'updated_on': utility_obj.get_local_time(data.get('updated_on')),
            'updated_by': str(data.get('updated_by')),
            'updated_by_name': data.get('updated_by_name'),
        }

