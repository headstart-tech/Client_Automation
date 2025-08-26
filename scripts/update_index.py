"""
MongoDB Index Management Script

This script connects to a MongoDB database, loads index specifications from a Python file, and ensures the specified
indexes are created on the appropriate collections in the database. It handles index creation, checks for existing
indexes, and logs the process.

Functions:
-----------
load_indexes_from_file(file_path):
    Loads index specifications from the specified file.

index_exist(collection, index):
    Checks if an index already exists in the collection.

fetch_db_indexes():
    Fetches existing indexes from the specified collection in the database.

create_indexes(collection, indexes):
    Creates indexes on a specified MongoDB collection if they do not already exist.

Usage:
------
1. Set the connection URI for your MongoDB instance in the `uri` variable.
2. Specify the database name in the `db` variable.
3. Provide the path to the index file in the `index_file` variable.
4. Run the script to ensure the indexes specified in the file are created in the database.
"""

import hashlib
import logging
import os
import importlib.util
from typing import Optional, Dict, List, Union
from pymongo import MongoClient

uri = "mongodb+srv://<username>:<password>@<db_url>/"
client = MongoClient(uri)
db = client['season_2024']
index_file = "season_2024.py"  # Replace with your file name that contains latest indexes


def load_indexes_from_file(file_path: str) -> Optional[Dict[str, List[Dict[str, Union[str, Dict[str, Union[str, int]]]]]]]:
    """
    Load indexes from a Python module file located at `file_path`.

    Params:
        file_path (str): File path to the Python module containing indexes.

    Returns:
        Optional[Dict[str, List[Dict[str, Union[str, Dict[str, Union[str, int]]]]]]]:
            Dictionary of indexes loaded from `file_path`, or `None` if file doesn't exist.

    Raises:
        Any exceptions that may occur during module loading.
    """
    if os.path.exists(file_path):
        spec = importlib.util.spec_from_file_location("indexes", file_path)
        index_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(index_module)
        return index_module.indexes
    else:
        logging.error(f"File {file_path} not found.")
        return None


def index_exist(collection: Dict[str, Dict[str, str]], index: Dict[str, Union[str, int]]) -> bool:
    """
    Check if an index already exists in the collection that matches the given fields.

    Params:
        collection (Dict[str, Dict[str, str]]): A dictionary where keys are index names and values are dictionaries of fields.
        index (Dict[str, Union[str, int]]): The index to check for existence in `collection`.

    Returns:
        bool: True if an index matching all fields in `index` exists in `collection`, False otherwise.
    """
    if dict(sorted(index.items())) in collection:
        return True
    else:
        return False


def fetch_db_indexes() -> List[Dict[str, str]]:
    """
    Fetch indexes that are already present in the specified collection.

    Returns:
        List[Dict[str, str]]: A list of dictionaries representing the indexes in the collection.
    """
    db_indexes = db[collection].index_information()
    formatted_index = []
    for index_name, index_details in db_indexes.items():
        if index_name == '_id_':
            continue
        output_dict = {key: value for key, value in index_details.get("key")}
        formatted_index.append(dict(sorted(output_dict.items())))
    return formatted_index


def create_indexes(collection: str, indexes: List[Dict[str, Union[str, Dict[str, Union[str, int]]]]]) -> None:
    """
    Create indexes on a specified MongoDB collection.

    Params:
        collection (str): Name of the MongoDB collection.
        indexes (List[Dict[str, Union[str, Dict[str, Union[str, int]]]]]): List of index definitions,
            where each dictionary contains keys for index creation.

    Returns:
        None
    """
    db_collections = db.list_collection_names()
    if collection in db_collections:
        formatted_indexes = fetch_db_indexes()
        for index in indexes:
            if not index_exist(formatted_indexes, index['keys']):
                index_name = hashlib.md5(index["name"].encode('utf-8')).hexdigest()
                try:
                    db[collection].create_index(index.get("keys"), name=index_name, unique=True if "type" in index else False)
                    logging.info(
                        f"Created index '{index_name}' on '{collection}' for field '{index}'.")
                except Exception as e:
                    logging.error(
                        f"Failed to create index '{index_name}' on '{collection}': {e}")
            else:
                logging.info(
                    f"Index with pattern {index['keys']} already exists in '{collection}'. Skipping.")
    else:
        logging.info(
            f"Collection {collection} doesn't exists in '{collection}'. Skipping.")


index_specifications: Optional[Dict[str, List[Dict[str, Union[str, Dict[str, Union[str, int]]]]]]] = load_indexes_from_file(index_file)

# Iterate through collections and create indexes as specified
for collection, indexes in index_specifications.items():
    create_indexes(collection, indexes)

logging.info("Index creation process completed.")
