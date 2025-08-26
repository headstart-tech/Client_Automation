"""
This file contains configuration related to background function
"""
import inspect
import traceback
import uuid
from functools import wraps
from typing import Any, Callable

from app.core.log_config import get_logger

logger = get_logger(name=__name__)


def background_task_wrapper(func: Callable) -> Callable:
    """
    Decorator to wrap asynchronous tasks, providing logging for task start, success, and failure.

    :param func: The asynchronous function to be wrapped
    :return: The wrapped function with added logging functionality
    """
    task_name = func.__name__

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> None:
        task_id = uuid.uuid4()

        # Format function arguments as a string
        func_args = inspect.signature(func).bind(*args, **kwargs).arguments
        func_args_str = ", ".join(
            "{}={!r}".format(*item) for item in func_args.items())

        # Log the start of the task with its arguments
        logger.debug(
            f"[{task_id}] Started {task_name} with arguments: {func_args_str}")

        try:
            # Execute the original function
            await func(*args, **kwargs)
            # Log the successful completion of the task
            logger.debug(f"[{task_id}] Finished {task_name} Successfully")
        except Exception as e:
            # Log the permanent failure of the task with the error
            # and traceback, this is not showing error code
            # tb_str = traceback.format_exception(etype=type(e),
            # value=e, tb=e.__traceback__)
            # logger.error(f"[{task_id}] Failed Permanently
            # {task_name} with error: {e}\n{''.join(tb_str)}")
            # raise e
            # This is showing error
            tb_str = traceback.format_exception(type(e), e, e.__traceback__)
            logger.error(
                f"[{task_id}] Failed Permanently {task_name}"
                f" with error: {e}\n{''.join(tb_str)}")
            raise e

    return wrapper
