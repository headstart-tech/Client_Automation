"""
This file contains schemas to student query
"""
from enum import Enum
from pydantic import BaseModel
from app.models.course_schema import ProgramFilter
from app.models.applications import DateRange


class QueryType(str, Enum):
    """
    Schema of query type
    """
    general_query = "General Query"
    payment_related_query = "Payment Related Query"
    application_query = "Application Query"
    other_query = "Other Query"


class GetQuery(BaseModel):
    """
    Schema for get queries.
    """
    program_names: list[ProgramFilter] | None = None
    date_range: DateRange | None = None
    search: str | None = None
    query_type: list[QueryType] | None = None
    sort: str | None = None
    sort_type: str | None = None
    counselor_ids: list[str] | None = None
    season: str | None = None
