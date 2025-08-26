"""
This file contains API route related to create query categories
"""
from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from app.core.utils import utility_obj
from app.database.configuration import DatabaseConfiguration

query_category_router = APIRouter()


@query_category_router.post("/", summary="Create query categories", deprecated=True)
async def create_query_categories():
    """
    Create query categories\n
    * :*return* **Query categories created successfully.**:
    """
    categories = [
        {"name": "General Query"},
        {"name": "Payment Related Query"},
        {"name": "Application Query"},
        {"name": "Other Query"},
    ]
    for i in categories:
        query_category = await DatabaseConfiguration().queryCategories.find_one({"name": i["name"]})
        if query_category:
            raise HTTPException(
                status_code=422, detail="Query categories already exists."
            )
    DatabaseConfiguration().queryCategories.insert_many(categories)
    return utility_obj.response_model(
        data=categories, message="Query categories created successfully."
    )
