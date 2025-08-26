# import os
# import sys
# from app.core.utils import settings
# os.listdir(".")
# if not os.path.isfile(".env"):
#     sys.exit("'.env' not found! Please add it and try again.")
# else:
#     print(" '.env' file found. Continuing execution ")

from app.core.log_config import CustomFileFormatter, CustomFormatter, get_logger

# TODO : Problem when running with main.py .env not found
