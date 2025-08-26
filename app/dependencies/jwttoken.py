"""
This file contain class and functions related to authentication using jwttoken
"""
from datetime import datetime, timedelta
from typing import Optional

from bson import ObjectId
from jose import JWTError, jwt

from app.core.log_config import get_logger
from app.core.utils import settings
from app.models.student_user_schema import TokenData

logger = get_logger(name=__name__)

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm_used
ACCESS_TOKEN_EXPIRE_DAYS = 1


class Authentication:
    """
    Contain functions related to authentication
    """

    REFRESH_TOKEN_EXPIRE_DAYS = 30

    async def create_refresh_token(self, data: dict):
        """
        Create a refresh token with a longer expiry than access tokens
        """
        try:
            to_encode = data.copy()
            today = datetime.utcnow()
            expire = datetime.utcnow() + timedelta(
                self.REFRESH_TOKEN_EXPIRE_DAYS)
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, SECRET_KEY,
                                     algorithm=ALGORITHM)
            return {"issued_at": today, "expiry_time": expire,
                    "refresh_token": encoded_jwt}
        except JWTError as e:
            logger.error(f"Failed to create refresh token."
                         f" Got JWTError. Error: {e}")
        except Exception as e:
            logger.error(f"Failed to create refresh token. Error: {e}")

    async def verify_refresh_token(self, token: str, credentials_exception):
        """
        Verify and return the token data of refresh token
        """
        # Don't move below statement in the top of a file otherwise we'll
        # get following error at the time of run test
        # cases, Error - Attached to different loop
        from app.database.configuration import DatabaseConfiguration
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")
            college_info: list = payload.get("college_info")
            if user_id is None or token_type != "refresh":
                raise credentials_exception
            if await DatabaseConfiguration().refresh_token_collection.find_one(
                    {"refresh_token": token, "revoked": True}):
                raise credentials_exception
            if (user := await DatabaseConfiguration(
            ).user_collection.find_one(
                {"_id": ObjectId(user_id)})) is not None:
                access_token = await self.create_access_token(
                    data={"sub": user.get("user_name"),
                          "scopes": [user.get("role", {}).get("role_name")],
                          "college_info": college_info, "user_id": user_id})
            else:
                student = await DatabaseConfiguration(
                ).studentsPrimaryDetails.find_one(
                    {"_id": ObjectId(user_id),
                     "college_id": ObjectId(college_info[0].get("_id"))})
                access_token = await self.create_access_token(
                    data={"sub": student.get("user_name"),
                          "scopes": ["student"], "college_info": college_info})
            return {
                "message": "New access token issued.",
                "access_token": access_token,
                "token_type": "bearer"
            }
        except JWTError as e:
            logger.error(f"Failed to verify refresh token."
                         f" Got JWTError. Error: {e}")
            raise credentials_exception
        except Exception as e:
            logger.error(f"Failed to verify refresh token. Error: {e}")
            raise credentials_exception

    async def revoke_refresh_token(self, token, credentials):
        """
        Revoke refresh token
        """
        # Don't move below statement in the top of a file otherwise we'll
        # get following error at the time of run test
        # cases, Error - Attached to different loop
        from app.database.configuration import DatabaseConfiguration
        refresh_token_data = await DatabaseConfiguration(
        ).refresh_token_collection.find_one({"refresh_token": token})
        if not refresh_token_data:
            raise credentials
        if refresh_token_data.get("revoked", False):
            return {"detail": "Refresh token is already revoked."}
        await DatabaseConfiguration().refresh_token_collection.update_one(
            {"refresh_token": token}, {
            "$set": {"revoked": True, "revoked_datetime": datetime.utcnow()}})
        return {"message": "Refresh token is revoked."}

    async def create_access_token(self, data: dict,
                                  expires_delta: Optional[timedelta] = None):
        """
        Get a JSON web token for authentication of user
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(ACCESS_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def create_access_token_with_out_async(self,
                                           data: dict,
                                           expires_delta: Optional[
                                               timedelta] = None):
        """
        Get a Json web token for authentication of user
        This function is not async function
        Params:
        data (dict): details given
        timedelta: how much time does this token stay alive
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(ACCESS_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def verify_token(self, token: str, credentials_exception,
                           websocket=False):
        # todo: need to validate role_id as well, role_id should not be None
        """
        Verify and return the token data of user
        """
        token_data = {}
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_name: str = payload.get("sub")
            role_id = payload.get("role_id", None)
            groups_info = payload.get("group_ids", [])
            if user_name is None:
                if websocket:
                    pass
                else:
                    raise credentials_exception
            token_scopes = payload.get("scopes", [])
            college_info = payload.get("college_info", [{}])
            if len(token_scopes) != 1:
                if websocket:
                    pass
                else:
                    raise credentials_exception
            token_data = TokenData(scopes=token_scopes, user_name=user_name,
                                   college_info=college_info, role_id=role_id, groups=groups_info)
        except JWTError:
            if websocket:
                pass
            else:
                raise credentials_exception
        return token_data

    async def get_token_details(self, token: str, credentials_exception):
        """
        Get token_details
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_name: str = payload.get("sub")
            if user_name is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        return payload

    def create_access_token_sync(self, data: dict,
                                 expires_delta: Optional[timedelta] = None):
        """
        Get a JSON web token for authentication of user
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(ACCESS_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
