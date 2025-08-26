"""
This file contain class and functions related to hash password and verify hash password
"""
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



class Hash:
    """
    Convert the normal password into hashed format
    And verifying whether hashed and normal password is same or not
    """

    def get_password_hash(self, password: str):
        """
        Hash the password
        """
        return pwd_context.hash(password)

    def verify_password(self, hashed, normal):
        """
        Verify the hash password and normal password
        """
        return pwd_context.verify(normal, hashed)
