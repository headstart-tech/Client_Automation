"""
MongoDB Index Synchronization Script

This script connects to production and development MongoDB databases, allowing you to synchronize indexes between them.
It provides options to add missing indexes from the production database to the development database and remove extra
indexes from the development database that are not present in the production database.

Functions:
-----------
get_collection_indexes(database, collection_name, get_names=False):
    Retrieves all indexes for a given collection in the specified database.
    If get_names is True, it includes index names in the output.

sync_indexes(source_db, target_db):
    Synchronizes indexes from the source database to the target database by adding missing indexes to the target.

delete_extra_indexes(source_db, target_db):
    Removes extra indexes from the target database that are not present in the source database.
"""


from pymongo import MongoClient
from typing import List, Dict, Union
import logging
from pymongo.database import Database

# MongoDB URIs and database names
prod_uri = "mongodb+srv://<username>:<password>@<db_url>/"
dev_uri = "mongodb+srv://<username>:<password>@<db_url>/"
database_name = "season_2024"  # Assuming the same database name for simplicity; adjust if they differ

# Connect to the MongoDB clusters
prod_client = MongoClient(prod_uri)
dev_client = MongoClient(dev_uri)

prod_db = prod_client[database_name]
dev_db = dev_client[database_name]  # Adjust if your dev database name is different


def get_collection_indexes(database, collection_name: str, get_names: bool = False) -> List[Dict[str, Union[str, Dict[str, int]]]]:
    """
    Retrieve all indexes for a given collection.

    Params:
        database: MongoDB database object.
        collection_name (str): Name of the MongoDB collection.
        get_names (bool, optional): Flag to include index names in the output dictionaries. Default is False.

    Returns:
        List[Dict[str, Union[str, Dict[str, int]]]]: A list of dictionaries, each representing an index in the collection.
            Each dictionary contains 'keys' representing the indexed fields, and optionally 'name' if get_names is True.
            If an index is unique, 'type' is included with the value "Unique Index".

    Raises:
        (Include any potential exceptions or errors that may occur during the retrieval process.)

    Notes:
        - The function retrieves index information using `index_information()` method of the MongoDB collection.
        - '_id_' index is skipped, as it's MongoDB's default primary index and typically not relevant for application logic.
    """
    index_data = database[collection_name].index_information()
    formatted_indexes = []
    for index_name, index_details in index_data.items():
        if index_name == '_id_':
            continue
        output_dict = {key: value for key, value in index_details.get("key")}
        if get_names:
            data_dict = {"name": index_name, "keys": dict(sorted(output_dict.items()))}
        else:
            data_dict = {"keys": dict(sorted(output_dict.items()))}
        if index_details.get('unique'):
            data_dict["type"] = "Unique Index"
        formatted_indexes.append(data_dict)
    return formatted_indexes


def sync_indexes(source_db: Database, target_db: Database) -> None:
    """
    Sync indexes from source_db to target_db.

    Params:
        source_db (Database): Source MongoDB database object.
        target_db (Database): Target MongoDB database object.

    Returns:
        None
    """
    for collection_name in source_db.list_collection_names():
        source_indexes = get_collection_indexes(source_db, collection_name, get_names=True)
        target_indexes = get_collection_indexes(target_db, collection_name)

        # Determine which indexes need to be created on the target
        missing_indexes = []
        for index in source_indexes:
            index_name = index.get("name")
            del index['name']
            if index not in target_indexes:
                if index.get("type"):
                    index_type = index["type"]
                    del index['type']
                    if index in target_indexes:
                        logging.info(
                            f"{index['keys']} present without unique property, recreating the same unique index.")
                        target_db[collection_name].drop_index(index_name)
                    index["type"] = index_type
                else:
                    index["type"] = "Unique Index"
                    if index in target_indexes:
                        logging.info(
                            f"{index['keys']} present with unique property, recreating the same non unique index.")
                        target_db[collection_name].drop_index(index_name)
                    del index["type"]
                missing_indexes.append(index)
        for index in missing_indexes:
            target_db[collection_name].create_index(index["keys"], unique=True if "type" in index else False)
            logging.info(f"{index['keys']} index is created for collection {collection_name}.")


def delete_extra_indexes(source_db: Database, target_db: Database) -> None:
    """
    Remove extra indexes from target_db.

    Params:
        source_db (Database): Source MongoDB database object.
        target_db (Database): Target MongoDB database object.

    Returns:
        None
    """
    for collection_name in source_db.list_collection_names():

        source_indexes = get_collection_indexes(source_db, collection_name)
        target_indexes = get_collection_indexes(target_db, collection_name, get_names=True)
        # Determine which indexes need to be created on the target
        extra_indexes = []
        for index in target_indexes:
            index_name = index.get("name")
            del index['name']
            if index not in source_indexes:
                if index.get("type"):
                    index_type = index["type"]
                    del index['type']
                    if index in source_indexes:
                        logging.info(
                            f"{index['keys']} present without unique property, recreating the same unique index.")
                        target_db[collection_name].drop_index(index_name)
                        target_db[collection_name].create_index(index["keys"], unique=True if "type" in index else False)
                        continue
                    index['type'] = index_type
                else:
                    index["type"] = "Unique Index"
                    if index in source_indexes:
                        logging.info(
                            f"{index['keys']} present with unique property, recreating the same non unique index.")
                        target_db[collection_name].drop_index(index_name)
                        target_db[collection_name].create_index(index["keys"], unique=True if "type" in index else False)
                        continue
                    del index["type"]
                index["name"] = index_name
                extra_indexes.append(index)
        for index in extra_indexes:
            target_db[collection_name].drop_index(index["name"])
            logging.info(f"{index['keys']} index is deleted from collection {collection_name}.")


while True:
    # Sync from production to development
    action = str(input("enter the function you want to perform\n 1. Enter '1' if you want to add indexes from production db to target db\n 2. Enter '2' if you want to remove unnecessary indexes from target db\n else enter exit :")).strip().lower()
    if action == "1":
        sync_indexes(prod_db, dev_db)
        logging.info("Index synchronization process completed.")
        break
    elif action == "2":
        delete_extra_indexes(prod_db, dev_db)
        logging.info(f"Extra indexes removed from {dev_db} successfully.")
        break
    elif action == "exit":
        break

# Optionally, you can also sync from development to production if needed
