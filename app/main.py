"""
Run the live server: on local system
Main Module for executing uvicorn server based on operating system .
"app.routers.api_v1.app:app" the object created inside of app

Multiple workers doesn't work on Windows
Container images created for Linux ARM64
"""
import os
import sys

# Adding PYTHONPATH  for Import Error This will set up PYTHONONPATH
# for absolute package imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tracemalloc
from sys import platform

import uvicorn

from app.core.log_config import get_logger

logger = get_logger(name=__name__)


def logit(log_message):
    """Logger info"""
    logger.info("Operating system = %s %s", platform, log_message)


def log_memory_usage():
    # Stop tracemalloc tracing and get a snapshot of the memory usage
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics("lineno")

    # Group the stats by filename
    grouped_stats = {}
    for stat in top_stats:
        key = stat.traceback[0].filename
        if key not in grouped_stats:
            grouped_stats[key] = stat.size
        else:
            grouped_stats[key] += stat.size

    # Sort the stats by memory usage and write them to a file
    sorted_stats = sorted(grouped_stats.items(), key=lambda x: x[1],
                          reverse=True)
    with open("memory_stats.txt", "w") as f:
        f.write("[ Top 10 memory consuming files ]\n")
        for stat in sorted_stats[:10]:
            f.write(f"{stat[0]}: {stat[1]} bytes\n")

    # Log the top 10 memory consuming files
    logger.info("[ Top 10 memory consuming files ]")
    for stat in sorted_stats[:10]:
        logger.info(f"{stat[0]}: {stat[1]} bytes")


def main():
    """Set logger and start app."""
    log_message = " and 4 workers are running."
    if platform in ["linux", "linux2"]:
        # Linux
        logit(log_message)
        # SystemInfo().system_information()
        uvicorn.run(
            "app.routers.api_v1.app:app",
            host="0.0.0.0",
            port=8000,
            workers=4,
            proxy_headers=True,
            forwarded_allow_ips="*",
        )
    elif platform == "darwin":
        # OS X
        logit(log_message)
        uvicorn.run(
            "app.routers.api_v1.app:app",
            host="0.0.0.0",
            port=8000,
            workers=4,
            proxy_headers=True,
            forwarded_allow_ips="*",
        )
    elif platform == "win32":
        # Windows...
        logit(" and 4 workers are disabled.")
        uvicorn.run(
            "app.routers.api_v1.app:app",
            host="0.0.0.0",
            port=8000,
            proxy_headers=True,
            forwarded_allow_ips="*",
        )


def run_with_tracemalloc(func):
    tracemalloc.start()
    func()
    log_memory_usage()


if __name__ == "__main__":
    # Uncomment the following line and comment the
    # 'run_with_tracemalloc(main)' line for local development
    run_with_tracemalloc(lambda: uvicorn.run("app.routers.api_v1.app:app"))
    # run_with_tracemalloc(main)
