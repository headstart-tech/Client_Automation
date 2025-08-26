# **MongoDB Index Fetching Script** (fetch_indexes.py)

This script is designed to connect to a specified MongoDB database and retrieve index information from all collections within that database. The retrieved index data is formatted and saved to a Python file in JSON format, with unique indexes specifically marked. The output file is named after the database, with a .py extension.

### **Functions**

* fetch_indexes_and_save(client, db_name)
* Fetches index information from all collections in a specified MongoDB database and saves it to a file.

### **Parameters:**

* **client** : pymongo.MongoClient, The MongoDB client instance used to connect to the database.
* **db_name** : str, The name of the MongoDB database from which to fetch index information.

### Usage

* Set the connection string for your MongoDB instance in the connection_string variable.
* Add the database names you want to process in the db_names list.
* Run the script. It will generate a .py file for each specified database, containing the index information for all collections in JSON format.

### Note

* This script skips the "id" index as it is the default index created by MongoDB for each collection.
* The script assumes the presence of the "unique" key in index details to identify unique indexes.

# MongoDB Index Sync Script (index_sync.py)

This script is designed to synchronize index information between two MongoDB databases. Specifically, it can copy 
indexes from a source database (e.g., a production database) to a target database (e.g., a development database), or it 
can remove extra indexes from the target database that are not present in the source database. The script provides 
detailed logging of the actions taken.

### Script Overview

### MongoDB URIs and Database Names

Define the connection strings and the database name:

* `prod_uri = "mongodb+srv://<username>:<password>@<db_url>/"`
* `dev_uri = "mongodb+srv://<username>:<password>@<db_url>/"`
* `database_name = "season_2024"`

Replace "username", "password", and "db_url" with your MongoDB credentials and URLs.

### Connecting to MongoDB Clusters

Establish connections to both the production and development MongoDB clusters:

* `prod_client = MongoClient(prod_uri)`
* `dev_client = MongoClient(dev_uri)`
* `prod_db = prod_client[database_name]`
* `dev_db = dev_client[database_name]`

## Functions

### get_collection_indexes(database, collection_name: str, get_names: bool = False)

Retrieves all indexes for a given collection in the specified database.

**Params:**
* `database`: MongoDB database object.
* `collection_name` (str): Name of the MongoDB collection.
* `get_names` (bool, optional): Flag to include index names in the output dictionaries.

**Returns**:
* List of dictionaries, each representing an index in the collection. Each dictionary contains 'keys' representing the indexed fields, and optionally 'name' if get_names is True. If an index is unique, 'type' is included with the value "Unique Index".

### sync_indexes(source_db: Database, target_db: Database)

Syncs indexes from the source database to the target database.

**Params**:
* `source_db` (Database): Source MongoDB database object.
* `target_db` (Database): Target MongoDB database object.

**Returns**:
* None

### delete_extra_indexes(source_db: Database, target_db: Database)

Removes extra indexes from the target database that are not present in the source database.

**Params**:
* `source_db` (Database): Source MongoDB database object.
* `target_db` (Database): Target MongoDB database object.

**Returns**:
* None

**Usage**
* Set the connection strings for your MongoDB instances.
* Adjust the database names if necessary.
* Run the script.
* Choose the desired action by following the prompts.

**Notes**
* The script uses the index_information() method of the MongoDB collection to retrieve index data.
* The script skips the "id" index as it is MongoDB's default primary index.
* It handles unique indexes and ensures that unique constraints are preserved during synchronization.

# MongoDB Index Initialization Script (init_index.py)

This script is designed to manage index specifications for MongoDB collections. It allows you to load index definitions 
from a file, add new index specifications to the file, and save these specifications back to the file. This can be useful 
for maintaining index configurations in a version-controlled manner.

## Script Overview

### Functions

`load_indexes_from_file(file_path: str) -> Optional[List[Dict[str, Union[str, Dict[str, int]]]]]`

Loads index specifications from a specified Python file.

**Parameters**:
* file_path (str): The path to the Python file containing the index definitions.

**Returns**:
* List of index specifications defined in the file, or None if the file does not exist.

`add_indexes(data: Dict[str, object], table_name: str, file_name: str) -> None`

Adds an index specification to a specified table in the index file.

**Parameters**:
* data (dict): The index data to be added. This should contain at least a "keys" field.
* table_name (str): The name of the table to which the index should be added.
* file_name (str): The path to the file containing the index specifications.

* **Returns**:
* None

`restore_file(indexes: Dict[str, object], file_name: str) -> None`

Saves the index specifications to a file.

**Parameters**:
* indexes (dict): The index specifications to be saved.
* file_name (str): The path to the file where the index specifications should be saved.

**Returns**:
* None

**Main Script**

The main script interacts with the user to gather index information and save it to the specified file.
1. `File Name and Table Name`: The script prompts the user to input the file name and table name for which the index is to be created.
2. `Unique Index`: The user is asked if the index is unique.
3. `Key Names and Types`: The user can enter multiple key names and their types (1 for ascending, -1 for descending).
4. `Index Name`: The user can specify a name for the index or let the script generate one.
5. `Add Index`: The gathered index data is added to the specified table in the file.

**Usage**
* Set the file_name to the path of the Python file containing your index specifications.
* Run the script.
* Follow the prompts to enter the table name, whether the index is unique, and the key names and types.
* Optionally, specify a name for the index.
* The script will add the index specifications to the file.

 **Notes**
* The script uses the importlib.util module to dynamically import the index specifications from a Python file.
* It handles unique indexes and ensures that duplicate indexes are not added.
* The restore_file function saves the index specifications in JSON format in the specified file.

# MongoDB Index Update Management Script (update_index.py)

This script is designed to manage index specifications for MongoDB collections. It loads index definitions from a file, 
checks if the indexes already exist in the database, and creates any missing indexes. This can be useful for maintaining 
index configurations in a version-controlled manner and ensuring that your database indexes are always up-to-date.

## Script Overview

### Functions

`load_indexes_from_file(file_path: str) -> Optional[Dict[str, List[Dict[str, Union[str, Dict[str, Union[str, int]]]]]]]`

Loads index specifications from a specified Python file

**Parameters**:
* **file_path** (str): The path to the Python file containing the index definitions.

**Returns**:
* Dictionary of index specifications defined in the file, or None if the file does not exist.

`index_exist(collection: Dict[str, Dict[str, str]], index: Dict[str, Union[str, int]]) -> bool`

Checks if an index already exists in the collection that matches the given fields.

**Parameters**:
* **collection** (Dict[str, Dict[str, str]]): A dictionary where keys are index names and values are dictionaries of fields.
* **index** (Dict[str, Union[str, int]]): The index to check for existence in collection.

**Returns**:
* `True` if an index matching all fields in `index` exists in `collection`, `False` otherwise.

`fetch_db_indexes(collection: str) -> List[Dict[str, str]]`

Fetches indexes that are already present in the specified collection.

**Parameters**:
* **collection** (str): Name of the MongoDB collection.

**Returns**:
* List of dictionaries representing the indexes in the collection.

`create_indexes(collection: str, indexes: List[Dict[str, Union[str, Dict[str, Union[str, int]]]]]) -> None`

Creates indexes on a specified MongoDB collection.

**Parameters**:
* **collection**  (str): Name of the MongoDB collection.
* **index** (List[Dict[str, Union[str, Dict[str, Union[str, int]]]]]): List of index definitions, where each dictionary contains keys for index creation.

**Returns**:
* None

## Main Script

The main script loads index specifications from a file, checks if they already exist in the database, and creates any missing indexes.

1. Database Connection: Connects to the MongoDB database using the specified URI.
2. Load Index Specifications: Loads the index specifications from the specified file.
3. Create Indexes: Iterates through the collections and creates indexes as specified, if they do not already exist.

**Usage**
* Set the uri variable to your MongoDB connection URI.
* Set the index_file variable to the path of the Python file containing your index specifications.
* Run the script.

**Notes**
* The script uses the importlib.util module to dynamically import the index specifications from a Python file.
* It handles unique indexes and ensures that duplicate indexes are not added.
* Indexes are created with a hashed name based on the provided name to avoid conflicts.

# season_2024.py

This file contains the index definitions for various collections used in the application. These indexes are crucial for 
optimizing database queries, ensuring efficient data retrieval, and maintaining data integrity.

This structured documentation provides a clear overview of each collection and its indexes, making it easier to 
understand the purpose and organization of the season_2024.py file.