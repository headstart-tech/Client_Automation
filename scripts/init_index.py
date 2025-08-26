"""
MongoDB Index Management Script

This script allows the user to add new index specifications to a Python file containing existing index definitions for a
MongoDB database. It ensures that the index does not already exist before adding it and saves the updated index
specifications back to the file.

Functions:
-----------
load_indexes_from_file(file_path):
    Loads index specifications from the specified Python file.

add_indexes(data, table_name, file_name):
    Adds an index specification to the specified table in the index file.

restore_file(indexes, file_name):
    Save the index specifications to a file.

Usage:
------
1. Set the file name containing the index specifications in the `file_name` variable.
2. Run the script and follow the prompts to input the table name, index uniqueness, key names, key types, and
    optionally the index name.
3. The script will update the index specifications file with the new index information.
"""

from pymongo import MongoClient
import json
import importlib.util
import os
import logging
from typing import List, Dict, Union, Optional


def load_indexes_from_file(file_path: str) -> Optional[List[Dict[str, Union[str, Dict[str, int]]]]]:
    """
    Load index specifications from a Python file.

    This function attempts to load a module from the specified file path and
    extract an 'indexes' attribute from the module. If the file does not exist,
    an error is logged and None is returned.

    Parameters:
    file_path (str): The path to the Python file containing the index definitions.

    Returns:
    list: The list of indexes defined in the file, or None if the file does not exist.
    """
    if os.path.exists(file_path):
        spec = importlib.util.spec_from_file_location("indexes", file_path)
        index_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(index_module)
        return index_module.indexes
    else:
        logging.error(f"File {file_path} not found.")
        return None


def add_indexes(data: Dict[str, object], table_name: str, file_name: str) -> None:
    """
    Add an index specification to the specified table in the index file.

    This function loads index specifications from a given file and adds a new
    index specification for the specified table. If an index with the same keys
    already exists, it logs an error and does not add the new index. If the table
    does not exist in the index specifications, it creates a new entry for the table
    with the provided index data.

    Parameters:
    data (dict): The index data to be added. This should contain at least a "keys" field.
    table_name (str): The name of the table to which the index should be added.
    file_name (str): The path to the file containing the index specifications.

    Returns:
    None
    """
    index_specifications: Optional[Dict[str, list]] = load_indexes_from_file(file_name)
    if index_specifications.get(table_name):
        for index_obj in index_specifications.get(table_name):
            if index_obj.get("keys") == data.get("keys"):
                logging.error("Index data already present")
                return
        else:
            index_specifications.get(table_name).append(data)
            restore_file(index_specifications, file_name)
            logging.info(f"New indexes created for table {table_name}")
    else:
        index_specifications[table_name] = [data]
        restore_file(index_specifications, file_name)
        logging.info(f"New indexes created for table {table_name}")


def restore_file(indexes: Dict[str, object], file_name: str) -> None:
    """
    Save the index specifications to a file.

    This function writes the given index specifications to a specified file in JSON format.
    It handles errors during the file writing process and logs appropriate messages.

    Parameters:
    indexes (dict): The index specifications to be saved.
    file_name (str): The path to the file where the index specifications should be saved.

    Returns:
    None
    """
    try:
        with open(file_name, 'w') as f:
            f.write("# Indexes data\n\n")
            f.write("indexes = ")
            json.dump(indexes, f, indent=4)
        logging.info(f"Indexes saved successfully")
    except Exception as e:
        logging.error(f"An error occurred: {e}, while while fetching indexes from file:{file_name}")
    return


if __name__ == "__main__":
    file_name = "season_2024.py"     # Replace with your file name that contains latest indexes
    table_name = str(input("Enter the table name, you want to create index for: "))
    is_unique_index_input = input("Is the index unique (True/False): ").strip().lower()
    is_unique_index = True if is_unique_index_input in ["true", 1, "yes"] else False
    keys = {}
    while True:
        key_name = str(input("Enter key name or type exit : "))
        if key_name == "exit":
            break
        key_type = int(input("Enter key type ('1' for asc and '-1' for desc) :"))
        keys[key_name] = key_type
    name = str(input("Do you want to give name to your index (Yes/No): ")).strip().lower()
    if name == "yes":
        name_value = str(input("Enter name for your index: "))
    else:
        name_value = '_'.join([f"{key}_{value}" for key, value in keys.items()])
    data= {}
    data["name"] = name_value
    data["keys"] = keys
    if is_unique_index:
        data["type"] = "Unique Index"
    add_indexes(data, table_name, file_name)
