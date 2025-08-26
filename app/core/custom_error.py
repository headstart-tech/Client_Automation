"""
This file create custom error using exception
"""


class ObjectIdInValid(Exception):
    """Raised Object id is not valid."""

    def __init__(self, _id, name,
                 message="must be a 12-byte input or a "
                         f"24-character hex string"):
        """
            Error Invalid object id.

            Params:
                _id (str): _id contains an interview list id
                        in string format.
                 name (str): name of the id related with the things.
                 message (str): message related to the Exception.

            Returns:
                raise (Exception): Error message, 500
        """
        self._id = _id
        self.name = name
        self.message = f"{self.name} `{self._id}` {message}"
        super().__init__(self.message)


class DataNotFoundError(Exception):
    """Raised when Application not found in the database."""

    def __init__(self, _id=None, message="Data"):
        """
            Error Data not found.

            Params:
                 message (str): message related to the Exception.

            Returns:
                raise (Exception): Error message, 500
        """
        self._id = _id
        self.message = f"{message} not found id: {_id}" \
            if self._id is not None else f"{message} not found"
        super().__init__(self.message)


class UserLimitExceeded(Exception):
    """Raised when Application not found in the database."""

    def __init__(self, message="User"):
        """
            Error Data not found.

            Params:
                 message (str): message related to the Exception.

            Returns:
                raise (Exception): Error message, 500
        """
        self.message = f"{message} limit exceeded"
        super().__init__(self.message)


class CustomError(Exception):
    """
    Raised when condition fails.
    """

    def __init__(self, message="Something went wrong."):
        """
            Error Something went wrong.

            Params:
                 message (str): message related to the Exception.

            Returns:
                Exception: Error message, 500
        """
        self.message = message
        super().__init__(message)


class NotEnoughPermission(Exception):
    """
    Helper class which useful for raise error when user don't have permission of particular thing/API.
    """

    def __init__(self, message="Not enough permissions"):
        """
        Error when user don't have permission of particular thing/API.

        Params:
             message (str): message related to the Exception.

        Returns:
            raise (Exception): Error message, 401
        """
        self.message = message
        super().__init__(message)
