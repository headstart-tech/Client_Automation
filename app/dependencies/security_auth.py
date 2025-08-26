"""
This file contains functions related to security auth
"""
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.core.log_config import get_logger

logger = get_logger(name=__name__)

security = HTTPBasic()
docs = APIRouter()


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Get the current logged-in username
    """
    correct_username = secrets.compare_digest(credentials.username, "sb")
    correct_password = secrets.compare_digest(
        credentials.password, "qtv3Bq7VaUR$9MeU754S"
    )
    if not (correct_username and correct_password):
        logger.error(f"UNAUTHORIZED Access")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
