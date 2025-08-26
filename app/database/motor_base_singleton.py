from app.database.master_db_connection import Master_db


class MotorBaseSingleton:
    """
    Singleton class that provides a single instance of MotorBase, a MongoDB client.

    Usage:
    >>> motor_base = MotorBaseSingleton.get_instance()
    """

    # The singleton instance is stored as a class variable
    __instance = None

    @staticmethod
    def get_instance():
        """
        Returns the singleton instance of MotorBase.

        If the instance has not been created yet, creates it and returns it.

        Returns:
            An instance of MotorBase.
        """
        if MotorBaseSingleton.__instance is None:
            MotorBaseSingleton()
        return MotorBaseSingleton.__instance

    def __init__(self, college_id=None, db_name=None):
        """
        Creates a new instance of MotorBase if one does not exist.

        Raises:
            Exception: if an instance of MotorBaseSingleton already exists.
        """
        if MotorBaseSingleton.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            MotorBaseSingleton.__instance = Master_db(college_id=college_id,
                                                      db_name=db_name)

    @staticmethod
    def clear_instance():
        MotorBaseSingleton.__instance = None

    @property
    def master_data(self):
        return self.__instance
