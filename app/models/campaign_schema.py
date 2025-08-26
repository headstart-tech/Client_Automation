"""
This file contain schemas related to campaign
"""
from pydantic import BaseModel

from app.models.automation import PerformAutomation, PerformAutomationBeta


class CreateCampaign(BaseModel):
    """
    Schema for create campaign
    """
    campaign_type: str
    campaign_name: str
    campaign_description: str = None
    filters: dict = None
    raw_data_name: str = None
    period: dict = None
    enabled: bool
    is_published: bool


class CreateCampaignRule(BaseModel):
    """
    Schema for create or update campaign rule
    """
    rule_name: str
    rule_description: str = None
    script: PerformAutomationBeta
    campaign_name: str
    enabled: bool
    is_published: bool


class Rule(BaseModel):
    """
    Schema for create automation
    """
    rule_name: str = None
    rule_description: str = None
    script: PerformAutomation = None
    data_segment_name: str = None
    enabled: bool = None
    is_published: bool = None
