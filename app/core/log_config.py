"""
This file contains configuration related to logging messages.
"""

import io
import logging
import os
import time
from logging import handlers
from pathlib import Path
from pathlib import PurePath

import tomli as tomllib
from fastapi.exceptions import HTTPException


class GetPathInfo:
    """A class to get TOML file data."""

    @classmethod
    def from_toml(cls):
        """
        Read the TOML file and return its contents as a dictionary.

        Returns:
            dict: The contents of the TOML file.

        Raises:
            HTTPException: If the TOML file has a wrong format.
            HTTPException: If the TOML file is not found.
        """
        toml_dict = {}
        try:
            with open(str(cls.get_toml_file_path()), "rb") as toml:
                toml_dict = tomllib.load(toml)
        except tomllib.TOMLDecodeError:
            raise HTTPException(status_code=403, detail="TOML file has wrong format!")
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail="File not found!")
        return toml_dict

    @classmethod
    def get_toml_file_path(cls):
        """
        Get the full path of the TOML file.

        Returns:
            PurePath: The full path of the TOML file.
        """
        path = Path(__file__).parent.parent.parent
        return PurePath(path, Path("config.toml"))


toml_data = GetPathInfo().from_toml()

LOG_LEVEL = toml_data.get("general", {}).get("log_level", "INFO")  # Default log level is INFO


class CustomFormatter(logging.Formatter):
    """
    Configure the format of logging messages with colors.
    """

    reset = "\x1b[0m"
    grey = "\x1b[38;5;240m"
    green = "\x1b[38;5;34m"
    yellow = "\x1b[38;5;220m"
    red = "\x1b[38;5;196m"
    purple = "\x1b[38;5;98m"
    blue = "\x1b[38;5;32m"
    cyan = "\x1b[38;5;50m"

    format = "%(levelname)-6s %(asctime)s - %(name)s - %(threadName)s - %(message)s (%(filename)s:%(lineno)d)"
    details_format = (
        "%(levelname)-6s %(asctime)s - %(name)s - %(threadName)s - %(message)s (%(filename)s:%(lineno)d) "
        "call_trace=%(pathname)s L%(lineno)-4d "
    )

    COLORS = {
        logging.DEBUG: purple,
        logging.INFO: cyan,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: blue,
    }

    FORMATS = {
        logging.DEBUG: format,
        logging.INFO: format,
        logging.WARNING: format,
        logging.ERROR: details_format,
        logging.CRITICAL: details_format,
    }

    def format(self, record):
        """
        Return logging message in respective format with colors.
        """
        color = self.COLORS.get(record.levelno)
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(f"{color}{log_fmt}{self.reset}")
        return formatter.format(record)


class CustomFileFormatter(logging.Formatter):
    """
    Configure the format of logging messages for file output.
    """

    details_format = "%(levelname)-6s %(asctime)s - %(name)s - %(threadName)s - %(message)s (%(filename)s:%(lineno)d)"

    process_info = "Process ID - %(process)d "
    processName = "Process name - %(processName)s "
    thread_id = "Thread ID - %(thread)d"
    thread_name = "Thread Name - %(threadName)s"
    call_trace = "call_trace=%(pathname)s L%(lineno)-4d"

    FORMATS = {
        logging.DEBUG: details_format,
        logging.INFO: details_format,
        logging.WARNING: f"{details_format} {call_trace}",
        logging.ERROR: f"{details_format} {thread_id} {thread_name} {call_trace}",
        logging.CRITICAL: f"{details_format} {processName} {process_info} {thread_name} {thread_id} {call_trace}",
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Return logging message in respective format for file output.
        """
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class __NullHandler(io.StringIO):
    """
    A NullHandler class for basic configuration of logging messages.
    """

    def emit(self, record):
        pass

    def write(self, *args, **kwargs):
        pass


def delete_old_logs(log_directory: str, days: int = 7):
    """
    Deletes log files in the given directory that are older than a certain number of days.

    :param log_directory: The directory where the log files are stored.
    :param days: The age of the log files to keep. Older files will be deleted.
    """
    now = time.time()

    for filename in os.listdir(log_directory):
        if filename.endswith(".log"):
            file_path = os.path.join(log_directory, filename)
            if os.path.getmtime(file_path) < now - days * 86400:  # 86400 seconds in a day
                os.remove(file_path)


def get_logger(
        name: str,
        filename: str = f"logs/GTCRM-{LOG_LEVEL}.log",
        when: str = "midnight",
        interval: int = 1,
        backup_count: int = 50,
        level: int = getattr(logging, LOG_LEVEL),
) -> logging.Logger:
    """
    Create and return a logger with the given name and configuration.

    :param name: The name of the logger.
    :param filename: The file path where logs will be stored.
    :param when: Determines the type of interval for log rotation.
    :param interval: The interval at which logs will be rotated.
    :param backup_count: The number of backup log files to keep.
    :param level: The logging level.
    :return: A configured logger instance.
    """
    log_directory = Path(filename).parent
    if not log_directory.exists():
        log_directory.mkdir(parents=True)
    else:
        delete_old_logs(str(log_directory))  # call the delete_old_logs function

    root = logging.root

    if not root.handlers:
        logging.basicConfig(level=level)

        # File handler for log rotation
        fh = handlers.TimedRotatingFileHandler(
            filename=filename,
            when=when,
            interval=interval,
            backupCount=backup_count,
        )
        fh.setLevel(level)
        fh.setFormatter(CustomFileFormatter())
        fh.suffix = "%d-%m-%Y.log"  # This line changes the suffix to the desired format
        root.addHandler(fh)

        # Stream handler for the visible output
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(CustomFormatter())
        root.addHandler(ch)

    return logging.getLogger(name)
