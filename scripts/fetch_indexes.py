"""
MongoDB Index Fetching Script

This script connects to a specified MongoDB database and retrieves index information from all collections within that
database. It formats the index data and saves it to a Python file in JSON format, marking unique indexes accordingly.
The output file is named after the database, with a .py extension.

Functions:
-----------
fetch_indexes_and_save(client, db_name):
    Fetches index information from all collections in a specified MongoDB database and saves it to a file.

Parameters:
-----------
client : pymongo.MongoClient
    The MongoDB client instance used to connect to the database.
db_name : str
    The name of the MongoDB database from which to fetch index information.

Usage:
------
1. Set the connection string for your MongoDB instance in the `connection_string` variable.
2. Add the database names you want to process in the `db_names` list.
3. Run the script. It will generate a .py file for each specified database, containing the index information for all
    collections in JSON format.

Note:
-----
- This script skips the "_id_" index as it is the default index created by MongoDB for each collection.
- The script assumes the presence of the "unique" key in index details to identify unique indexes.
"""

from pymongo import MongoClient
import json
from typing import Dict, Union
import logging


def fetch_indexes_and_save(client: MongoClient, db_name: str) -> None:
    """
    Fetch index information from all collections in a MongoDB database and save it to a file.

    This function connects to the specified MongoDB database, retrieves index information
    from all collections, formats the index data, and saves it to a Python file in JSON format.
    Unique indexes are marked as such in the output.

    Parameters:
    client (pymongo.MongoClient): The MongoDB client instance.
    db_name (str): The name of the MongoDB database from which to fetch index information.

    Returns:
    None
    """
    db = client[db_name]
    indexes = {}

    collections = db.list_collection_names()
    for collection_name in collections:
        collection = db[collection_name]
        index_info = collection.index_information()
        formatted_indexes = []
        for index_name, index_details in index_info.items():
            if index_name == '_id_':
                continue
            output_dict = {key: value for key, value in index_details.get("key")}
            data_dict = {"name": index_name,"keys": output_dict}
            if index_details.get('unique'):
                data_dict["type"] = "Unique Index"
            formatted_indexes.append(data_dict)
        if formatted_indexes:
            indexes[collection_name] = formatted_indexes
    if indexes:
        file_name = f"{db_name}.py"
        try:
            with open(file_name, 'w') as f:
                f.write("# Indexes data\n\n")
                f.write("indexes = ")
                json.dump(indexes, f, indent=4)
            logging.info(f"Data has been saved to {file_name}")
        except Exception as e:
            logging.error(f"An error occurred: {e}, while while fetching indexes from file:{file_name}")
    return


if __name__ == "__main__":
    connection_string = "mongodb+srv://<username>:<password>@<db_url>/"  # Replace with your connection string
    client = MongoClient(connection_string)
    db_names = ["season_2024"]  # Replace with your db_name that contains latest indexes
    for db_name in db_names:
        if db_name == "local" or db_name == "admin":
            continue
        fetch_indexes_and_save(client, db_name)
